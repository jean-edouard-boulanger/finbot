"""Subscribe side of the event bus: the Postgres listener and the per-worker websocket fan-out.

The publish side lives in `finbot.core.events` and is synchronous, so it can be called from Temporal
activities. Everything asyncio-flavoured is here.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from finbot.apps.appwsrv.events.hub import EventHub
from finbot.apps.appwsrv.events.listener import EventListener

logger = logging.getLogger(__name__)

#: One hub and one listener per uvicorn worker process. Module-level because the websocket route and the
#: application lifespan both need to reach the same instance.
event_hub = EventHub()
event_listener = EventListener(event_hub)


@asynccontextmanager
async def events_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run the Postgres listener for as long as the application is up.

    Note that in development `tools/run-web-service.sh` restarts workers with SIGKILL, so the shutdown half
    of this never runs; the listener DSN sets TCP keepalives so Postgres reaps the orphaned backend.
    """
    event_listener.start(asyncio.get_running_loop())
    try:
        yield
    finally:
        event_listener.stop()
