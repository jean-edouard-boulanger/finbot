from datetime import datetime
from typing import Any

from pydantic import Field

from finbot.core.schema import BaseModel
from finbot.core.utils import now_utc

# Postgres NOTIFY channel every finbot event travels on. Subscribers filter by `user_account_id`.
EVENTS_CHANNEL = "finbot_events"

# Postgres caps a NOTIFY payload at 8000 bytes. Staying comfortably under leaves room for the channel name
# and protocol overhead; anything larger degrades to a REFETCH event.
MAX_PAYLOAD_BYTES = 7000


class EventType:
    """Event types carried on the bus.

    Not an enum: the bus is deliberately open, and the websocket forwards types it does not know about so
    that adding a producer does not require touching the transport.
    """

    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_UPDATED = "notification.updated"
    NOTIFICATION_RESOLVED = "notification.resolved"
    NOTIFICATION_READ = "notification.read"
    NOTIFICATION_DISMISSED = "notification.dismissed"
    VALUATION_UPDATED = "valuation.updated"
    #: Application-level keepalive. Sent by the websocket, never published to the bus -- some intermediaries
    #: drop an idle connection without closing it, and this is what makes that visible to both ends.
    PING = "ping"
    # "Something changed but the details did not fit (or were lost): re-read over REST." Every degradation
    # path in the bus collapses to this, which is what lets the socket stay a hint channel.
    REFETCH = "refetch"


class Event(BaseModel):
    type: str
    user_account_id: int
    #: Monotonic within a producer (a notification or snapshot id). Lets a client discard an event it has
    #: already applied, and identifies what moved.
    seq: int
    #: Postgres collapses byte-identical NOTIFY payloads raised within a single transaction (verified: three
    #: identical sends arrive as one). Microsecond-resolution `emitted_at` is what keeps two genuinely
    #: distinct events from serialising identically and being silently merged -- do not drop this field, and
    #: do not round it.
    emitted_at: datetime = Field(default_factory=now_utc)
    data: dict[str, Any] = Field(default_factory=dict)
