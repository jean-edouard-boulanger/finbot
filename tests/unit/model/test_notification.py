from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from finbot.model import Notification, SessionType, UserAccount


def make_user_account(session: SessionType, email: str = "test@finbot.dev") -> UserAccount:
    user_account = UserAccount(
        email=email,
        password_hash=b"hash",
        full_name="Test User",
    )
    session.add(user_account)
    session.commit()
    return user_account


def make_notification(
    user_account_id: int,
    dedup_key: str | None,
    status: str = "active",
    **kwargs,
) -> Notification:
    return Notification(
        user_account_id=user_account_id,
        notification_type="linked_account_failure",
        severity="warning",
        status=status,
        dedup_key=dedup_key,
        title="Barclays hasn't synced since Tuesday",
        occurrences=1,
        last_seen_at=datetime.now(timezone.utc),
        **kwargs,
    )


def test_notification_can_be_persisted(db_session: SessionType):
    user_account = make_user_account(db_session)
    db_session.add(make_notification(user_account.id, "linked_account_failure:1"))
    db_session.commit()

    stored = db_session.query(Notification).one()
    assert stored.occurrences == 1
    assert stored.dismissed_at is None
    assert stored.created_at is not None


def test_two_open_notifications_with_same_dedup_key_are_rejected(db_session: SessionType):
    """The partial unique index is what makes aggregation an invariant rather than a convention."""
    user_account = make_user_account(db_session)
    db_session.add(make_notification(user_account.id, "linked_account_failure:1"))
    db_session.commit()

    db_session.add(make_notification(user_account.id, "linked_account_failure:1"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_dismissing_reopens_the_dedup_key(db_session: SessionType):
    """Dismissal closes the aggregation window: the next occurrence gets a brand new notification."""
    user_account = make_user_account(db_session)
    dismissed = make_notification(
        user_account.id,
        "linked_account_failure:1",
        dismissed_at=datetime.now(timezone.utc),
    )
    db_session.add(dismissed)
    db_session.commit()

    db_session.add(make_notification(user_account.id, "linked_account_failure:1"))
    db_session.commit()

    assert db_session.query(Notification).count() == 2


def test_resolved_notification_still_holds_the_dedup_key(db_session: SessionType):
    """A resolved notification stays visible until dismissed, so it must keep blocking a duplicate row.

    This is the reason the index predicate tests only `dismissed_at`: were `status` part of it, the user
    would end up looking at a 'resolved' and an 'active' card for the same source simultaneously.
    """
    user_account = make_user_account(db_session)
    resolved = make_notification(
        user_account.id,
        "linked_account_failure:1",
        status="resolved",
        resolved_at=datetime.now(timezone.utc),
    )
    db_session.add(resolved)
    db_session.commit()

    db_session.add(make_notification(user_account.id, "linked_account_failure:1"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_notifications_without_dedup_key_never_conflict(db_session: SessionType):
    """NULLs do not conflict in a btree, so ad-hoc notifications insert freely."""
    user_account = make_user_account(db_session)
    db_session.add(make_notification(user_account.id, None))
    db_session.add(make_notification(user_account.id, None))
    db_session.commit()

    assert db_session.query(Notification).count() == 2


def test_same_dedup_key_across_users_does_not_conflict(db_session: SessionType):
    first = make_user_account(db_session, email="first@finbot.dev")
    second = make_user_account(db_session, email="second@finbot.dev")
    db_session.add(make_notification(first.id, "linked_account_failure:1"))
    db_session.add(make_notification(second.id, "linked_account_failure:1"))
    db_session.commit()

    assert db_session.query(Notification).count() == 2
