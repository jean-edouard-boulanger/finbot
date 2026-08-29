import asyncio

import pytest

from finbot.apps.appwsrv.events.hub import SUBSCRIBER_QUEUE_SIZE, EventHub
from finbot.core.events import Event, EventType


def make_event(user_account_id: int = 1, seq: int = 1) -> Event:
    return Event(type=EventType.NOTIFICATION_CREATED, user_account_id=user_account_id, seq=seq)


@pytest.mark.asyncio
async def test_event_reaches_its_subscriber():
    hub = EventHub()
    queue = hub.subscribe(1)

    hub.dispatch(make_event(user_account_id=1, seq=7))

    assert queue.get_nowait().seq == 7


@pytest.mark.asyncio
async def test_events_are_not_delivered_to_other_users():
    hub = EventHub()
    queue = hub.subscribe(1)

    hub.dispatch(make_event(user_account_id=2))

    assert queue.empty()


@pytest.mark.asyncio
async def test_every_subscriber_of_a_user_gets_the_event():
    """One user with several tabs open."""
    hub = EventHub()
    first = hub.subscribe(1)
    second = hub.subscribe(1)

    hub.dispatch(make_event(user_account_id=1))

    assert not first.empty()
    assert not second.empty()


@pytest.mark.asyncio
async def test_unsubscribing_stops_delivery():
    hub = EventHub()
    queue = hub.subscribe(1)
    hub.unsubscribe(1, queue)

    hub.dispatch(make_event(user_account_id=1))

    assert queue.empty()
    assert hub.subscriber_count == 0


@pytest.mark.asyncio
async def test_slow_subscriber_is_told_to_refetch_rather_than_growing_the_queue():
    """A backgrounded tab must never grow memory in the server.

    On overflow the backlog is dropped and replaced by a single refetch marker; ordinary queueing then
    resumes, so what the client eventually reads is "start over, then here is what happened since".
    """
    overflow = 5
    hub = EventHub()
    queue = hub.subscribe(1)

    for seq in range(SUBSCRIBER_QUEUE_SIZE + overflow):
        hub.dispatch(make_event(user_account_id=1, seq=seq))

    assert queue.qsize() <= SUBSCRIBER_QUEUE_SIZE, "the queue must stay bounded"
    assert queue.qsize() == overflow, "the backlog is dropped, not accumulated"
    assert queue.get_nowait().type == EventType.REFETCH, "the client is told to start over"
    assert all(queue.get_nowait().type != EventType.REFETCH for _ in range(queue.qsize()))


@pytest.mark.asyncio
async def test_malformed_payload_is_discarded_not_raised():
    """A bad payload must not take down the listener thread."""
    hub = EventHub()
    queue = hub.subscribe(1)

    hub.dispatch_payload("not json at all")
    hub.dispatch_payload('{"type": "x"}')  # valid json, missing required fields

    assert queue.empty()


@pytest.mark.asyncio
async def test_dispatch_payload_delivers_a_well_formed_event():
    hub = EventHub()
    queue = hub.subscribe(42)

    hub.dispatch_payload(make_event(user_account_id=42, seq=9).model_dump_json())

    assert queue.get_nowait().seq == 9


@pytest.mark.asyncio
async def test_reconnect_tells_everyone_to_refetch():
    """Events raised while the listener was down are gone, so clients must re-read over REST."""
    hub = EventHub()
    first = hub.subscribe(1)
    second = hub.subscribe(2)

    hub.broadcast_refetch()

    assert first.get_nowait().type == EventType.REFETCH
    assert second.get_nowait().type == EventType.REFETCH


@pytest.mark.asyncio
async def test_queue_is_bounded():
    hub = EventHub()
    queue = hub.subscribe(1)
    assert queue.maxsize == SUBSCRIBER_QUEUE_SIZE
    assert isinstance(queue, asyncio.Queue)
