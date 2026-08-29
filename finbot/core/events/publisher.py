import logging

from sqlalchemy import text

from finbot.core.events.schema import EVENTS_CHANNEL, MAX_PAYLOAD_BYTES, Event, EventType
from finbot.model import SessionType

logger = logging.getLogger(__name__)


def publish(session: SessionType, event: Event) -> None:
    """Queue `event` for delivery to subscribed websocket clients.

    NOTIFY is transactional: the payload is only delivered when the surrounding transaction commits, and is
    discarded on rollback. That is the point -- an event can never describe a row that was rolled back -- but
    it also means **the caller must commit**. `ScopedSession.__exit__` rolls back unconditionally, so an
    uncommitted publish is silently dropped: no error, no log, no event.

    Never raises. A publishing failure must not fail the valuation that produced it; the client refetches
    over REST on its next reconnect, so a lost event costs latency rather than correctness.
    """
    try:
        payload = event.model_dump_json()
        if len(payload.encode()) > MAX_PAYLOAD_BYTES:
            logger.warning(
                f"event payload too large for NOTIFY ({len(payload.encode())} bytes, type={event.type}), "
                f"degrading to '{EventType.REFETCH}'"
            )
            payload = Event(
                type=EventType.REFETCH,
                user_account_id=event.user_account_id,
                seq=event.seq,
            ).model_dump_json()
        session.execute(
            text("select pg_notify(:channel, :payload)"),
            {"channel": EVENTS_CHANNEL, "payload": payload},
        )
    except Exception:
        logger.exception(f"failed to publish event (type={event.type}, user_account_id={event.user_account_id})")
