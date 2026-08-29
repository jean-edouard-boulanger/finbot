from datetime import datetime, timezone

import pytest

from finbot.core.events import EVENTS_CHANNEL, MAX_PAYLOAD_BYTES, Event, EventType, publish
from finbot.core.inbox import (
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    STATUS_ACTIVE,
    STATUS_RESOLVED,
    dismiss_open_notification,
    raise_notification,
    resolve_notification,
)
from finbot.model import Notification, SessionType, UserAccount

DEDUP_KEY = "linked_account_failure:1"


@pytest.fixture
def user_account_id(db_session: SessionType) -> int:
    user_account = UserAccount(
        email="test@finbot.dev",
        password_hash=b"hash",
        full_name="Test User",
    )
    db_session.add(user_account)
    db_session.commit()
    return int(user_account.id)


def raise_failure(session: SessionType, user_account_id: int, **kwargs) -> Notification:
    return raise_notification(
        session,
        user_account_id=user_account_id,
        notification_type="linked_account_failure",
        severity=SEVERITY_WARNING,
        title="Barclays hasn't synced since Tuesday",
        dedup_key=DEDUP_KEY,
        **kwargs,
    ).notification


def resolve_failure(session: SessionType, user_account_id: int, **kwargs) -> bool:
    return resolve_notification(
        session,
        user_account_id=user_account_id,
        dedup_key=DEDUP_KEY,
        title="Barclays is syncing again",
        **kwargs,
    )


def test_first_occurrence_opens_a_notification(db_session: SessionType, user_account_id: int):
    result = raise_notification(
        db_session,
        user_account_id=user_account_id,
        notification_type="linked_account_failure",
        severity=SEVERITY_WARNING,
        title="Barclays hasn't synced since Tuesday",
        dedup_key=DEDUP_KEY,
    )

    assert result.created is True
    assert result.applied is True
    assert result.notification.occurrences == 1
    assert result.notification.status == STATUS_ACTIVE
    assert db_session.query(Notification).count() == 1


def test_repeat_occurrences_aggregate_onto_one_notification(db_session: SessionType, user_account_id: int):
    raise_failure(db_session, user_account_id)
    raise_failure(db_session, user_account_id)
    result = raise_notification(
        db_session,
        user_account_id=user_account_id,
        notification_type="linked_account_failure",
        severity=SEVERITY_WARNING,
        title="Barclays hasn't synced since Tuesday",
        dedup_key=DEDUP_KEY,
    )

    assert result.created is False
    assert db_session.query(Notification).count() == 1
    assert result.notification.occurrences == 3


def test_repeat_occurrence_re_marks_as_unread(db_session: SessionType, user_account_id: int):
    """A problem that is still live earns the badge again, even once read."""
    notification = raise_failure(db_session, user_account_id)
    notification.read_at = datetime.now(timezone.utc)
    db_session.commit()

    raise_failure(db_session, user_account_id)

    assert db_session.query(Notification).one().read_at is None


def test_resolving_flips_the_notification_in_place(db_session: SessionType, user_account_id: int):
    raise_failure(db_session, user_account_id)

    assert resolve_failure(db_session, user_account_id) is True

    stored = db_session.query(Notification).one()
    assert stored.status == STATUS_RESOLVED
    assert stored.resolved_at is not None
    assert stored.dismissed_at is None, "a resolved notification stays visible until dismissed"
    assert stored.title == "Barclays is syncing again"
    assert stored.read_at is None, "recovery is news even if the failure had been read"


def test_resolving_with_nothing_open_is_a_no_op(db_session: SessionType, user_account_id: int):
    assert resolve_failure(db_session, user_account_id) is False
    assert db_session.query(Notification).count() == 0


def test_resolving_twice_is_a_no_op(db_session: SessionType, user_account_id: int):
    raise_failure(db_session, user_account_id)

    assert resolve_failure(db_session, user_account_id) is True
    assert resolve_failure(db_session, user_account_id) is False


def test_problem_recurring_after_resolution_reuses_the_same_row(db_session: SessionType, user_account_id: int):
    """A resolved notification still holds the dedup key, so the user never sees two cards for one source."""
    raise_failure(db_session, user_account_id)
    resolve_failure(db_session, user_account_id)

    result = raise_notification(
        db_session,
        user_account_id=user_account_id,
        notification_type="linked_account_failure",
        severity=SEVERITY_WARNING,
        title="Barclays hasn't synced since Tuesday",
        dedup_key=DEDUP_KEY,
    )

    assert result.created is False
    assert db_session.query(Notification).count() == 1
    assert result.notification.status == STATUS_ACTIVE
    assert result.notification.resolved_at is None


def test_dismissing_closes_the_aggregation_window(db_session: SessionType, user_account_id: int):
    """Acknowledging means the next occurrence is reported afresh rather than silently bumping a count."""
    notification = raise_failure(db_session, user_account_id)
    raise_failure(db_session, user_account_id)
    notification.dismissed_at = datetime.now(timezone.utc)
    db_session.commit()

    result = raise_notification(
        db_session,
        user_account_id=user_account_id,
        notification_type="linked_account_failure",
        severity=SEVERITY_WARNING,
        title="Barclays hasn't synced since Tuesday",
        dedup_key=DEDUP_KEY,
    )

    assert result.created is True
    assert result.notification.occurrences == 1
    assert db_session.query(Notification).count() == 2


def test_notifications_without_a_dedup_key_never_aggregate(db_session: SessionType, user_account_id: int):
    for _ in range(3):
        raise_notification(
            db_session,
            user_account_id=user_account_id,
            notification_type="ad_hoc",
            severity=SEVERITY_ERROR,
            title="Something happened",
        )

    assert db_session.query(Notification).count() == 3


def test_stale_raise_is_fenced_out(db_session: SessionType, user_account_id: int):
    """A late-committing older snapshot must not overwrite what a newer one already established."""
    raise_failure(db_session, user_account_id, fencing_snapshot_id=10)

    result = raise_notification(
        db_session,
        user_account_id=user_account_id,
        notification_type="linked_account_failure",
        severity=SEVERITY_WARNING,
        title="stale title that must not land",
        dedup_key=DEDUP_KEY,
        fencing_snapshot_id=9,
    )

    assert result.applied is False
    stored = db_session.query(Notification).one()
    assert stored.occurrences == 1
    assert stored.title == "Barclays hasn't synced since Tuesday"


def test_stale_resolve_is_fenced_out(db_session: SessionType, user_account_id: int):
    """Without fencing, an overlapping refresh could permanently strand a broken account as 'resolved'."""
    raise_failure(db_session, user_account_id, fencing_snapshot_id=10)

    assert resolve_failure(db_session, user_account_id, fencing_snapshot_id=9) is False
    assert db_session.query(Notification).one().status == STATUS_ACTIVE


def test_newer_snapshot_is_applied(db_session: SessionType, user_account_id: int):
    raise_failure(db_session, user_account_id, fencing_snapshot_id=10)

    assert resolve_failure(db_session, user_account_id, fencing_snapshot_id=11) is True
    assert db_session.query(Notification).one().status == STATUS_RESOLVED


def test_publish_stages_a_notify_on_the_events_channel(db_session: SessionType):
    publish(db_session, Event(type=EventType.VALUATION_UPDATED, user_account_id=1, seq=1))
    db_session.commit()  # NOTIFY only fires on commit; this must not raise


def test_oversized_payload_degrades_to_refetch(db_session: SessionType, monkeypatch: pytest.MonkeyPatch):
    """A payload too large for NOTIFY must still tell the client that something moved."""
    captured: list[str] = []

    def capture(_session, statement, params):
        captured.append(params["payload"])

    monkeypatch.setattr(SessionType, "execute", capture)
    publish(
        db_session,
        Event(
            type=EventType.NOTIFICATION_CREATED,
            user_account_id=1,
            seq=1,
            data={"blob": "x" * (MAX_PAYLOAD_BYTES + 1)},
        ),
    )

    assert len(captured) == 1
    assert EventType.REFETCH in captured[0]
    assert "xxxx" not in captured[0]


def test_distinct_events_in_one_transaction_are_not_collapsed(db_session: SessionType):
    """Postgres merges byte-identical NOTIFY payloads raised in one transaction.

    `emitted_at` is what keeps two real events distinct. If it is ever dropped or rounded, two notifications
    raised in the same activity would silently arrive as one.
    """
    first = Event(type=EventType.NOTIFICATION_CREATED, user_account_id=1, seq=1)
    second = Event(type=EventType.NOTIFICATION_CREATED, user_account_id=1, seq=1)

    assert first.model_dump_json() != second.model_dump_json()


def test_events_channel_is_stable():
    """The listener LISTENs on this literal; changing it silently breaks delivery."""
    assert EVENTS_CHANNEL == "finbot_events"


def test_dismiss_open_notification_closes_the_window(db_session: SessionType, user_account_id: int):
    """Freezing or deleting an account dismisses its open notification so it cannot nag forever."""
    raise_failure(db_session, user_account_id)

    assert dismiss_open_notification(db_session, user_account_id=user_account_id, dedup_key=DEDUP_KEY) is True

    stored = db_session.query(Notification).one()
    assert stored.dismissed_at is not None


def test_dismiss_open_notification_with_nothing_open_is_a_no_op(db_session: SessionType, user_account_id: int):
    assert dismiss_open_notification(db_session, user_account_id=user_account_id, dedup_key=DEDUP_KEY) is False
