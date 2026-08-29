import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError

from finbot.core.events import Event, EventType, publish
from finbot.core.utils import now_utc
from finbot.model import Notification, SessionType

logger = logging.getLogger(__name__)

STATUS_ACTIVE = "active"
STATUS_RESOLVED = "resolved"

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"
SEVERITY_SUCCESS = "success"


@dataclass
class RaiseResult:
    notification: Notification
    #: True when this opened a new notification rather than bumping an existing one. Callers use it to
    #: distinguish "this problem just started" from "this problem is still going".
    created: bool
    #: False when a fencing check rejected the write because a more recent snapshot already had its say.
    applied: bool


def _find_open(session: SessionType, user_account_id: int, dedup_key: str) -> Notification | None:
    """Lock the open notification for this key, if there is one.

    `FOR UPDATE` serialises concurrent bumps of the same row, but it cannot lock a row that does not exist --
    two transactions finding nothing will both try to insert. The partial unique index catches that case and
    the caller retries; the lock and the index are complements, not alternatives.
    """
    notification: Notification | None = (
        session.query(Notification)
        .filter(
            Notification.user_account_id == user_account_id,
            Notification.dedup_key == dedup_key,
            Notification.dismissed_at.is_(None),  # type: ignore[no-untyped-call]
        )
        .with_for_update()
        .one_or_none()
    )
    return notification


def _is_fenced(notification: Notification, fencing_snapshot_id: int | None) -> bool:
    """True when this write describes an older snapshot than the one already recorded.

    Valuations are not serialised per user: a manual refresh overlapping a scheduled run produces concurrent
    workflows that can commit in either order. Without this check, a scoped run reporting "account 7 failed"
    could land after a full run reporting "account 7 succeeded" and strand the notification in the wrong
    state indefinitely. `UserAccountSnapshot.id` is a monotonic serial, so it works as a free fencing token.
    """
    if fencing_snapshot_id is None or notification.last_snapshot_id is None:
        return False
    return bool(fencing_snapshot_id <= notification.last_snapshot_id)


def _stage_event(session: SessionType, notification: Notification, event_type: str) -> None:
    """Queue the event announcing this change, to be delivered when the caller commits.

    Deliberately not committed here: NOTIFY only fires on COMMIT, so staging the event inside the same
    transaction as the row write is what guarantees subscribers never see an event for a row that was rolled
    back. The notification must already have been flushed, so that its id is assigned.
    """
    publish(
        session,
        Event(
            type=event_type,
            user_account_id=notification.user_account_id,
            seq=notification.id,
            data={"notification_id": notification.id},
        ),
    )


def raise_notification(
    session: SessionType,
    *,
    user_account_id: int,
    notification_type: str,
    severity: str,
    title: str,
    body: str | None = None,
    dedup_key: str | None = None,
    payload: dict[str, Any] | None = None,
    fencing_snapshot_id: int | None = None,
) -> RaiseResult:
    """Report a problem, aggregating repeat occurrences onto a single notification.

    With a `dedup_key`, the first occurrence opens a notification and subsequent ones bump its `occurrences`
    and refresh its copy. Dismissing closes that window, so the next occurrence opens a fresh notification.

    Commits before returning. **Never call this inside a `persist_scope` block**: that context manager commits
    on exit, and a nested commit here would flush a half-built object graph belonging to the caller. This is
    why linked-account notifications are produced by their own activity rather than from inside the snapshot
    builder, which runs under `persist_scope(new_snapshot)`.
    """
    now = now_utc()

    def build() -> Notification:
        return Notification(
            user_account_id=user_account_id,
            notification_type=notification_type,
            severity=severity,
            status=STATUS_ACTIVE,
            dedup_key=dedup_key,
            title=title,
            body=body,
            payload=payload,
            occurrences=1,
            last_seen_at=now,
            last_snapshot_id=fencing_snapshot_id,
        )

    if dedup_key is None:
        notification = build()
        session.add(notification)
        session.flush()
        _stage_event(session, notification, EventType.NOTIFICATION_CREATED)
        session.commit()
        return RaiseResult(notification=notification, created=True, applied=True)

    existing = _find_open(session, user_account_id, dedup_key)
    if existing is None:
        notification = build()
        try:
            with session.begin_nested():
                session.add(notification)
                session.flush()
        except IntegrityError:
            # Another writer opened this notification between our lookup and our insert. Drop what we have
            # and take the row they created, then fall through to the bump path.
            session.rollback()
            existing = _find_open(session, user_account_id, dedup_key)
            if existing is None:  # pragma: no cover - the unique index guarantees the row is there
                raise
        else:
            _stage_event(session, notification, EventType.NOTIFICATION_CREATED)
            session.commit()
            return RaiseResult(notification=notification, created=True, applied=True)

    if _is_fenced(existing, fencing_snapshot_id):
        logger.info(
            f"ignoring stale notification raise for {dedup_key} "
            f"(snapshot {fencing_snapshot_id} <= {existing.last_snapshot_id})"
        )
        session.rollback()
        return RaiseResult(notification=existing, created=False, applied=False)

    existing.occurrences = existing.occurrences + 1
    existing.severity = severity
    existing.status = STATUS_ACTIVE
    existing.title = title
    existing.body = body
    existing.payload = payload
    existing.last_seen_at = now
    existing.resolved_at = None
    # The problem is still live, so it earns the badge again even if the user has already read it.
    existing.read_at = None
    if fencing_snapshot_id is not None:
        existing.last_snapshot_id = fencing_snapshot_id
    session.flush()
    _stage_event(session, existing, EventType.NOTIFICATION_UPDATED)
    session.commit()
    return RaiseResult(notification=existing, created=False, applied=True)


def resolve_notification(
    session: SessionType,
    *,
    user_account_id: int,
    dedup_key: str,
    title: str,
    body: str | None = None,
    payload: dict[str, Any] | None = None,
    fencing_snapshot_id: int | None = None,
) -> bool:
    """Mark a problem as gone, flipping its notification in place.

    The notification is not deleted: it stays visible, in a resolved state, until the user dismisses it, so
    that a problem which fixed itself overnight is still reported rather than silently vanishing.

    Returns False when there was nothing to resolve, when it was already resolved, or when a more recent
    snapshot already had its say.
    """
    existing = _find_open(session, user_account_id, dedup_key)
    if existing is None or existing.status == STATUS_RESOLVED:
        session.rollback()
        return False

    if _is_fenced(existing, fencing_snapshot_id):
        logger.info(
            f"ignoring stale notification resolve for {dedup_key} "
            f"(snapshot {fencing_snapshot_id} <= {existing.last_snapshot_id})"
        )
        session.rollback()
        return False

    now = now_utc()
    existing.status = STATUS_RESOLVED
    existing.severity = SEVERITY_SUCCESS
    existing.title = title
    existing.body = body
    existing.payload = payload
    existing.resolved_at = now
    existing.last_seen_at = now
    # Recovery is news even if the failure had already been read.
    existing.read_at = None
    if fencing_snapshot_id is not None:
        existing.last_snapshot_id = fencing_snapshot_id
    session.flush()
    _stage_event(session, existing, EventType.NOTIFICATION_RESOLVED)
    session.commit()
    return True


def dismiss_open_notification(
    session: SessionType,
    *,
    user_account_id: int,
    dedup_key: str,
) -> bool:
    """Dismiss the open notification for this key, if there is one.

    For problems that stopped being tracked rather than getting fixed -- e.g. a failing linked account the
    user then freezes or deletes. Resolving would claim the problem went away; leaving it open would nag
    forever, since the account is excluded from future snapshots and nothing will ever update it.

    Commits before returning; never call inside a `persist_scope` block.
    """
    existing = _find_open(session, user_account_id, dedup_key)
    if existing is None:
        session.rollback()
        return False
    existing.dismissed_at = now_utc()
    session.flush()
    _stage_event(session, existing, EventType.NOTIFICATION_DISMISSED)
    session.commit()
    return True
