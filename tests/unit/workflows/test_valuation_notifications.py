from typing import Any

import pytest

from finbot.core.inbox import STATUS_ACTIVE, STATUS_RESOLVED
from finbot.model import (
    LinkedAccount,
    LinkedAccountSnapshotEntry,
    Notification,
    Provider,
    SessionType,
    SnapshotStatus,
    UserAccount,
    UserAccountSettings,
    UserAccountSnapshot,
)
from finbot.workflows.user_account_valuation.notifications import (
    describe_error,
    linked_account_dedup_key,
    sync_linked_account_notifications,
)

BARCLAYS = 1
KRAKEN = 2


@pytest.fixture
def user_account_id(db_session: SessionType) -> int:
    user_account = UserAccount(email="test@finbot.dev", password_hash=b"hash", full_name="Test User")
    db_session.add(user_account)
    db_session.flush()
    db_session.add(UserAccountSettings(user_account_id=user_account.id, valuation_ccy="GBP"))
    db_session.add(
        Provider(id="dummy_uk", description="Dummy", website_url="https://example.com", credentials_schema={})
    )
    db_session.flush()
    for linked_account_id, name in ((BARCLAYS, "Barclays"), (KRAKEN, "Kraken")):
        db_session.add(
            LinkedAccount(
                id=linked_account_id,
                user_account_id=user_account.id,
                provider_id="dummy_uk",
                account_name=name,
                account_colour="#000000",
            )
        )
    db_session.commit()
    return int(user_account.id)


def take_snapshot(db_session: SessionType, user_account_id: int, outcomes: dict[int, Any]) -> int:
    """Persist a snapshot recording `{linked_account_id: failure_details or None}` for the accounts touched."""
    snapshot = UserAccountSnapshot(
        user_account_id=user_account_id,
        status=SnapshotStatus.Success,
        requested_ccy="GBP",
    )
    db_session.add(snapshot)
    db_session.flush()
    for linked_account_id, failure_details in outcomes.items():
        db_session.add(
            LinkedAccountSnapshotEntry(
                snapshot_id=snapshot.id,
                linked_account_id=linked_account_id,
                success=failure_details is None,
                failure_details=failure_details,
            )
        )
    db_session.commit()
    return int(snapshot.id)


AUTH_FAILURE = [{"scope": "linked_account", "error": {"user_message": "nope", "error_code": "P001"}}]
UNKNOWN_FAILURE = [{"scope": "linked_account", "error": {"user_message": "boom", "error_code": "X002"}}]


def test_failing_account_raises_a_notification(db_session: SessionType, user_account_id: int):
    snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: AUTH_FAILURE, KRAKEN: None})

    outcome = sync_linked_account_notifications(db_session, user_account_id, snapshot_id)

    assert outcome.newly_failed_linked_account_ids == [BARCLAYS]
    notification = db_session.query(Notification).one()
    assert notification.dedup_key == linked_account_dedup_key(BARCLAYS)
    assert notification.title == "Barclays hasn't synced"
    assert notification.body == "Sign-in was rejected."
    assert notification.status == STATUS_ACTIVE


def test_payload_carries_what_the_dashboard_needs_to_quote(db_session: SessionType, user_account_id: int):
    """The panel writes a sentence about money, so it must not have to fan out extra requests."""
    take_snapshot(db_session, user_account_id, {BARCLAYS: None})
    snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: AUTH_FAILURE})

    sync_linked_account_notifications(db_session, user_account_id, snapshot_id)

    payload = db_session.query(Notification).one().payload
    assert payload["linked_account_id"] == BARCLAYS
    assert payload["account_name"] == "Barclays"
    assert payload["error_code"] == "P001"
    assert payload["valuation_ccy"] == "GBP"
    assert payload["last_success_at"] is not None, "the UI dates staleness from this, not from created_at"


def test_repeated_failures_aggregate(db_session: SessionType, user_account_id: int):
    for _ in range(3):
        snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: AUTH_FAILURE})
        sync_linked_account_notifications(db_session, user_account_id, snapshot_id)

    notification = db_session.query(Notification).one()
    assert notification.occurrences == 3


def test_recovery_resolves_the_notification(db_session: SessionType, user_account_id: int):
    snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: AUTH_FAILURE})
    sync_linked_account_notifications(db_session, user_account_id, snapshot_id)

    snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: None})
    outcome = sync_linked_account_notifications(db_session, user_account_id, snapshot_id)

    assert outcome.newly_resolved_linked_account_ids == [BARCLAYS]
    notification = db_session.query(Notification).one()
    assert notification.status == STATUS_RESOLVED
    assert notification.title == "Barclays is syncing again"
    assert notification.dismissed_at is None, "resolved notifications stay visible until dismissed"


def test_healthy_account_alone_raises_nothing(db_session: SessionType, user_account_id: int):
    snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: None, KRAKEN: None})

    outcome = sync_linked_account_notifications(db_session, user_account_id, snapshot_id)

    assert outcome == type(outcome)()
    assert db_session.query(Notification).count() == 0


def test_scoped_refresh_leaves_untouched_accounts_alone(db_session: SessionType, user_account_id: int):
    """A single-account refresh must not resolve a different account it never looked at."""
    snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: AUTH_FAILURE, KRAKEN: UNKNOWN_FAILURE})
    sync_linked_account_notifications(db_session, user_account_id, snapshot_id)
    assert db_session.query(Notification).count() == 2

    scoped_snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: None})
    sync_linked_account_notifications(db_session, user_account_id, scoped_snapshot_id)

    by_key = {n.dedup_key: n for n in db_session.query(Notification).all()}
    assert by_key[linked_account_dedup_key(BARCLAYS)].status == STATUS_RESOLVED
    assert by_key[linked_account_dedup_key(KRAKEN)].status == STATUS_ACTIVE


def test_out_of_order_snapshots_do_not_strand_a_broken_account(db_session: SessionType, user_account_id: int):
    """A manual refresh overlapping a scheduled run can commit late; it must not win.

    Both snapshots exist; the older one just reports its (stale) success after the newer one has already
    recorded the failure. Without fencing it would resolve the notification and the broken account would go
    quiet until the next scheduled run.
    """
    older_snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: None})
    newer_snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: AUTH_FAILURE})
    assert older_snapshot_id < newer_snapshot_id

    sync_linked_account_notifications(db_session, user_account_id, newer_snapshot_id)
    sync_linked_account_notifications(db_session, user_account_id, older_snapshot_id)

    assert db_session.query(Notification).one().status == STATUS_ACTIVE


def test_error_codes_become_sentences():
    assert describe_error("Barclays", "P001") == "Sign-in was rejected."
    assert describe_error("Barclays", "P004") == "This account needs reconfiguring."
    assert describe_error("Barclays", "X002") == "Finbot couldn't reach Barclays."
    assert describe_error("Barclays", None) == "Finbot couldn't reach Barclays."


def test_error_sentences_never_leak_internals():
    """Whatever the provider threw, the user reads plain language -- diagnostics live in settings."""
    for code in ("P001", "P002", "P004", "X002", "G001", None):
        sentence = describe_error("Barclays", code)
        assert "Error" not in sentence
        assert "Exception" not in sentence
        assert code is None or code not in sentence


def test_frozen_account_never_raises_a_notification(db_session: SessionType, user_account_id: int):
    """An account frozen while its snapshot was in flight must not be nagged about."""
    snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: AUTH_FAILURE})
    db_session.query(LinkedAccount).filter_by(id=BARCLAYS).update({"frozen": True})
    db_session.commit()

    outcome = sync_linked_account_notifications(db_session, user_account_id, snapshot_id)

    assert outcome == type(outcome)()
    assert db_session.query(Notification).count() == 0


def test_deleted_account_never_raises_a_notification(db_session: SessionType, user_account_id: int):
    snapshot_id = take_snapshot(db_session, user_account_id, {BARCLAYS: AUTH_FAILURE})
    db_session.query(LinkedAccount).filter_by(id=BARCLAYS).update({"deleted": True})
    db_session.commit()

    outcome = sync_linked_account_notifications(db_session, user_account_id, snapshot_id)

    assert outcome == type(outcome)()
    assert db_session.query(Notification).count() == 0
