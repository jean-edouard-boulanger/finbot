import asyncio
import logging
from collections import defaultdict

import orjson

from finbot.core.events import Event, EventType

logger = logging.getLogger(__name__)

#: Frames a single connection may fall behind by before it is told to refetch instead. A backgrounded tab on
#: a bad connection must never grow memory in the server.
SUBSCRIBER_QUEUE_SIZE = 64


class EventHub:
    """In-process fan-out from the Postgres listener to the websockets attached to this worker.

    One of these exists per uvicorn worker process. Every worker receives every event and filters by user
    here, which is fine at this scale and keeps the listener a single connection per process.
    """

    def __init__(self) -> None:
        self._subscribers: dict[int, set[asyncio.Queue[Event]]] = defaultdict(set)

    def subscribe(self, user_account_id: int) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE_SIZE)
        self._subscribers[user_account_id].add(queue)
        return queue

    def unsubscribe(self, user_account_id: int, queue: asyncio.Queue[Event]) -> None:
        subscribers = self._subscribers.get(user_account_id)
        if subscribers is None:
            return
        subscribers.discard(queue)
        if not subscribers:
            del self._subscribers[user_account_id]

    @property
    def subscriber_count(self) -> int:
        return sum(len(queues) for queues in self._subscribers.values())

    def dispatch_payload(self, raw_payload: str) -> None:
        """Handle one NOTIFY payload. Called from the listener thread via `loop.call_soon_threadsafe`."""
        try:
            event = Event.model_validate(orjson.loads(raw_payload))
        except Exception:
            logger.exception("discarding malformed event payload")
            return
        self.dispatch(event)

    def dispatch(self, event: Event) -> None:
        for queue in list(self._subscribers.get(event.user_account_id, ())):
            _offer(queue, event)

    def broadcast_refetch(self) -> None:
        """Tell every attached client to re-read over REST.

        Used after the listener reconnects: events raised while it was down are gone for good, so the only
        honest thing to say is "you may have missed something".
        """
        for user_account_id, queues in list(self._subscribers.items()):
            for queue in list(queues):
                _offer(queue, Event(type=EventType.REFETCH, user_account_id=user_account_id, seq=0))


def _offer(queue: asyncio.Queue[Event], event: Event) -> None:
    try:
        queue.put_nowait(event)
    except asyncio.QueueFull:
        # This connection is not keeping up. Drop what it has not read and leave it a single instruction to
        # start over -- the same degradation path as an oversized payload.
        _drain(queue)
        try:
            queue.put_nowait(Event(type=EventType.REFETCH, user_account_id=event.user_account_id, seq=0))
        except asyncio.QueueFull:  # pragma: no cover - just drained, so there is room
            logger.warning("dropped event for a subscriber that could not be drained")


def _drain(queue: asyncio.Queue[Event]) -> None:
    while True:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            return
