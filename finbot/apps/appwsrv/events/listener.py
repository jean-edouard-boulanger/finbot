import asyncio
import logging
import select
import threading

import psycopg2
import psycopg2.extensions

from finbot.apps.appwsrv.events.hub import EventHub
from finbot.core import environment
from finbot.core.events import EVENTS_CHANNEL

logger = logging.getLogger(__name__)

#: How long the socket wait blocks before re-checking the stop flag. Bounds shutdown latency, nothing else.
POLL_INTERVAL_SECONDS = 1.0

RECONNECT_BACKOFF_SECONDS = (1.0, 2.0, 5.0, 10.0, 30.0)


class EventListener:
    """Bridges Postgres LISTEN into this worker's asyncio loop.

    Runs in a daemon thread rather than on the loop: psycopg2 is synchronous, and a thread blocked in
    `select()` costs nothing. Using the existing driver avoids pulling a second Postgres client into the
    image for a component that issues no queries.
    """

    def __init__(self, hub: EventHub) -> None:
        self._hub = hub
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="finbot-events-listener", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=5.0)
            self._thread = None

    def _run(self) -> None:
        attempt = 0
        first_connection = True
        while not self._stop.is_set():
            connection = None
            try:
                connection = psycopg2.connect(environment.get_database_dsn())
                # LISTEN registers for the lifetime of a transaction, so the connection must not be inside
                # one -- without autocommit the registration is rolled back and nothing is ever delivered.
                connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                with connection.cursor() as cursor:
                    cursor.execute(f"LISTEN {EVENTS_CHANNEL}")
                logger.info(f"listening for events on '{EVENTS_CHANNEL}'")
                if not first_connection:
                    # Anything raised while we were disconnected is unrecoverable, so attached clients are
                    # told to re-read rather than being left with a stale panel.
                    self._call_on_loop(self._hub.broadcast_refetch)
                first_connection = False
                attempt = 0
                self._consume(connection)
            except Exception:
                if self._stop.is_set():
                    break
                delay = RECONNECT_BACKOFF_SECONDS[min(attempt, len(RECONNECT_BACKOFF_SECONDS) - 1)]
                logger.exception(f"event listener connection lost, reconnecting in {delay}s")
                attempt += 1
                self._stop.wait(delay)
            finally:
                if connection is not None:
                    try:
                        connection.close()
                    except Exception:
                        logger.debug("failed to close event listener connection", exc_info=True)
        logger.info("event listener stopped")

    def _consume(self, connection: psycopg2.extensions.connection) -> None:
        while not self._stop.is_set():
            if not select.select([connection], [], [], POLL_INTERVAL_SECONDS)[0]:
                continue
            connection.poll()
            while connection.notifies:
                payload = connection.notifies.pop(0).payload
                self._call_on_loop(self._hub.dispatch_payload, payload)

    def _call_on_loop(self, callback: object, *args: object) -> None:
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        try:
            loop.call_soon_threadsafe(callback, *args)  # type: ignore[arg-type]
        except RuntimeError:
            # The loop shut down between our check and this call; nothing left to deliver to.
            logger.debug("event loop closed while dispatching event")
