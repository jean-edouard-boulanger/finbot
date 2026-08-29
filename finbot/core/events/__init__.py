"""Generic per-user event bus, carried over Postgres LISTEN/NOTIFY.

The publish side lives here and is deliberately synchronous, so it can be called from Temporal activities and
from HTTP routes alike. The subscribe side is in `finbot.apps.appwsrv.events`, which is where asyncio and the
websocket fan-out live.

Delivery is at-most-once and best-effort: the socket is a hint channel, and REST remains the source of truth.
Clients refetch on connect and on every reconnect, so a dropped event costs latency, never correctness.
"""

from finbot.core.events.publisher import publish
from finbot.core.events.schema import EVENTS_CHANNEL, MAX_PAYLOAD_BYTES, Event, EventType

__all__ = [
    "EVENTS_CHANNEL",
    "MAX_PAYLOAD_BYTES",
    "Event",
    "EventType",
    "publish",
]
