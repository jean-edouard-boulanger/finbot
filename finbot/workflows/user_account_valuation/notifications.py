"""Turns snapshot outcomes into the in-app notifications a user sees on the dashboard.

Kept out of `user_account_snapshot.impl`, which builds the snapshot tree inside a `persist_scope` block:
the inbox service commits, and committing there would flush a half-built object graph. Reading the persisted
snapshot back afterwards is both simpler and safer.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func

from finbot.core.inbox import SEVERITY_ERROR, SEVERITY_WARNING, raise_notification, resolve_notification
from finbot.core.utils import some
from finbot.model import (
    LinkedAccountSnapshotEntry,
    LinkedAccountValuationHistoryEntry,
    SessionType,
    UserAccountSettings,
)

logger = logging.getLogger(__name__)

LINKED_ACCOUNT_FAILURE = "linked_account_failure"
VALUATION_FAILURE = "user_account_valuation_failure"

VALUATION_FAILURE_DEDUP_KEY = "user_account_valuation_failure"


def linked_account_dedup_key(linked_account_id: int) -> str:
    return f"{LINKED_ACCOUNT_FAILURE}:{linked_account_id}"


# Provider error codes, from finbot.providers.errors. Mapped to something a person can act on: the raw
# message and stack trace stay in the linked-account settings page, which the notification links to.
_ERROR_SENTENCES = {
    "P001": "Sign-in was rejected.",
    "P002": "This provider is no longer supported.",
    "P004": "This account needs reconfiguring.",
}


def describe_error(provider_name: str, error_code: str | None) -> str:
    sentence = _ERROR_SENTENCES.get(error_code or "")
    if sentence is not None:
        return sentence
    return f"Finbot couldn't reach {provider_name}."


@dataclass
class SyncOutcome:
    newly_failed_linked_account_ids: list[int] = field(default_factory=list)
    still_failing_linked_account_ids: list[int] = field(default_factory=list)
    newly_resolved_linked_account_ids: list[int] = field(default_factory=list)


def _first_error_code(failure_details: Any) -> str | None:
    """Pull an error code out of the serialised `[{scope, error}, ...]` written by the snapshot builder."""
    if not isinstance(failure_details, list):
        return None
    for entry in failure_details:
        if not isinstance(entry, dict):
            continue
        error = entry.get("error")
        if isinstance(error, dict) and error.get("error_code"):
            return str(error["error_code"])
    return None


def _last_success_times(session: SessionType, linked_account_ids: list[int]) -> dict[int, datetime]:
    if not linked_account_ids:
        return {}
    rows = (
        session.query(
            LinkedAccountSnapshotEntry.linked_account_id,
            func.max(LinkedAccountSnapshotEntry.created_at),
        )
        .filter(LinkedAccountSnapshotEntry.linked_account_id.in_(linked_account_ids))
        .filter_by(success=True)
        .group_by(LinkedAccountSnapshotEntry.linked_account_id)
        .all()
    )
    return {row[0]: row[1] for row in rows}


def _last_known_valuations(session: SessionType, linked_account_ids: list[int]) -> dict[int, float]:
    """Most recent valuation recorded for each account -- the money still counted in net worth while stale."""
    if not linked_account_ids:
        return {}
    latest = (
        session.query(
            LinkedAccountValuationHistoryEntry.linked_account_id.label("lid"),
            func.max(LinkedAccountValuationHistoryEntry.history_entry_id).label("hid"),
        )
        .filter(LinkedAccountValuationHistoryEntry.linked_account_id.in_(linked_account_ids))
        .group_by(LinkedAccountValuationHistoryEntry.linked_account_id)
        .subquery()
    )
    rows = (
        session.query(
            LinkedAccountValuationHistoryEntry.linked_account_id,
            LinkedAccountValuationHistoryEntry.valuation,
        )
        .join(  # type: ignore[no-untyped-call]
            latest,
            and_(
                LinkedAccountValuationHistoryEntry.linked_account_id == latest.c.lid,
                LinkedAccountValuationHistoryEntry.history_entry_id == latest.c.hid,
            ),
        )
        .all()
    )
    return {row[0]: float(row[1]) for row in rows}


def sync_linked_account_notifications(
    session: SessionType,
    user_account_id: int,
    snapshot_id: int,
) -> SyncOutcome:
    """Reconcile notifications against what a snapshot actually found.

    The snapshot's own entries are the set of accounts this run touched, which is what makes scoped
    single-account refreshes work without extra bookkeeping: an account absent from the snapshot is simply
    left alone rather than being wrongly resolved.
    """
    outcome = SyncOutcome()
    entries: list[LinkedAccountSnapshotEntry] = (
        session.query(LinkedAccountSnapshotEntry).filter_by(snapshot_id=snapshot_id).all()
    )
    if not entries:
        return outcome

    failed = [entry for entry in entries if not entry.success]
    succeeded = [entry for entry in entries if entry.success]

    settings: UserAccountSettings | None = (
        session.query(UserAccountSettings).filter_by(user_account_id=user_account_id).one_or_none()
    )
    valuation_ccy = settings.valuation_ccy if settings else None

    failed_ids = [some(entry.linked_account_id) for entry in failed]
    last_success_times = _last_success_times(session, failed_ids)
    last_known_valuations = _last_known_valuations(session, failed_ids)

    for entry in failed:
        linked_account = entry.linked_account
        # The snapshot pipeline excludes frozen and deleted accounts up front, but an account can be frozen
        # or deleted while a snapshot is in flight; its entry still lands here. Nagging about an account the
        # user has already shelved is worse than saying nothing.
        if linked_account.frozen or linked_account.deleted:
            continue
        linked_account_id = some(entry.linked_account_id)
        error_code = _first_error_code(entry.failure_details)
        provider_name = linked_account.account_name
        last_success_at = last_success_times.get(linked_account_id)
        result = raise_notification(
            session,
            user_account_id=user_account_id,
            notification_type=LINKED_ACCOUNT_FAILURE,
            severity=SEVERITY_WARNING,
            # Deliberately timeless: how stale the data is drifts with the clock, so the age and the amount
            # at risk are rendered client-side from the payload rather than frozen into a string here.
            title=f"{provider_name} hasn't synced",
            body=describe_error(provider_name, error_code),
            dedup_key=linked_account_dedup_key(linked_account_id),
            payload={
                "linked_account_id": linked_account_id,
                "provider_id": linked_account.provider_id,
                "account_name": linked_account.account_name,
                "error_code": error_code,
                "last_success_at": last_success_at.isoformat() if last_success_at else None,
                "last_known_value": last_known_valuations.get(linked_account_id),
                "valuation_ccy": valuation_ccy,
            },
            fencing_snapshot_id=snapshot_id,
        )
        if not result.applied:
            continue
        if result.created:
            outcome.newly_failed_linked_account_ids.append(linked_account_id)
        else:
            outcome.still_failing_linked_account_ids.append(linked_account_id)

    for entry in succeeded:
        if entry.linked_account.frozen or entry.linked_account.deleted:
            continue
        linked_account_id = some(entry.linked_account_id)
        resolved = resolve_notification(
            session,
            user_account_id=user_account_id,
            dedup_key=linked_account_dedup_key(linked_account_id),
            title=f"{entry.linked_account.account_name} is syncing again",
            payload={
                "linked_account_id": linked_account_id,
                "provider_id": entry.linked_account.provider_id,
                "account_name": entry.linked_account.account_name,
            },
            fencing_snapshot_id=snapshot_id,
        )
        if resolved:
            outcome.newly_resolved_linked_account_ids.append(linked_account_id)

    return outcome


def raise_valuation_failure_notification(
    session: SessionType,
    user_account_id: int,
    reason: str,
    fencing_snapshot_id: int | None = None,
) -> None:
    """Report a valuation that fell over outright.

    `RunValuationForAllUsers` swallows per-user exceptions, so without this a user whose valuation crashes
    gets no signal at all -- the dashboard just quietly stops moving.

    `fencing_snapshot_id` is the snapshot this run had already created when it failed, if any: valuations
    are not serialised per user, so a slow run reporting failure can otherwise land after a faster concurrent
    run already reported success. Passing it lets `raise_notification` ignore a report that is older than
    what is already on record. It is `None` when the run failed before a snapshot row existed to fence on --
    that gap is inherent to a run that never got far enough to have an identity to fence with.
    """
    raise_notification(
        session,
        user_account_id=user_account_id,
        notification_type=VALUATION_FAILURE,
        severity=SEVERITY_ERROR,
        title="Finbot couldn't refresh your accounts",
        # `reason` is whatever the orchestrator raised ("Child Workflow execution failed" and the like):
        # accurate for debugging, meaningless to the person reading it. It goes in the payload instead.
        body="Your figures are still the ones from the last successful refresh. Finbot will try again "
        "at the next scheduled sync.",
        dedup_key=VALUATION_FAILURE_DEDUP_KEY,
        payload={"reason": reason},
        fencing_snapshot_id=fencing_snapshot_id,
    )


def resolve_valuation_failure_notification(
    session: SessionType,
    user_account_id: int,
    fencing_snapshot_id: int | None = None,
) -> None:
    """Clear a standing valuation-failure notification now that a run has completed successfully.

    Fenced the same way `raise_valuation_failure_notification` is: without it, a faster concurrent run's
    success could clear a failure notification raised by a still-in-flight (or more recent) failing run,
    silently hiding a real, ongoing problem.
    """
    resolve_notification(
        session,
        user_account_id=user_account_id,
        dedup_key=VALUATION_FAILURE_DEDUP_KEY,
        title="Finbot is refreshing your accounts again",
        fencing_snapshot_id=fencing_snapshot_id,
    )
