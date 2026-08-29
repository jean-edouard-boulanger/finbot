import logging
from typing import Annotated

from fastapi import APIRouter, Path, Query

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.http_base import CurrentUserIdDep
from finbot.core.errors import NotAllowedError, ResourceNotFoundError
from finbot.core.events import Event, EventType, publish
from finbot.core.utils import now_utc
from finbot.model import Notification, db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/accounts/{user_account_id}/notifications",
    tags=["User accounts (notifications)"],
)

#: The panel shows what still needs attention plus recent history, not an audit log. Anything older falls off
#: the list and is reachable only until the retention job removes it.
DEFAULT_LIMIT = 50


def _unread_count(user_account_id: int) -> int:
    count: int = (
        db.session.query(Notification)
        .filter_by(user_account_id=user_account_id)
        .filter(
            Notification.dismissed_at.is_(None),  # type: ignore[no-untyped-call]
            Notification.read_at.is_(None),  # type: ignore[no-untyped-call]
        )
        .count()
    )
    return count


@router.get("/", operation_id="get_notifications")
def get_notifications(
    user_account_id: int,
    current_user_id: CurrentUserIdDep,
    limit: Annotated[int, Query(ge=1, le=200)] = DEFAULT_LIMIT,
) -> appwsrv_schema.GetNotificationsResponse:
    """Get in-app notifications for this user account"""
    if user_account_id != current_user_id:
        raise NotAllowedError()
    notifications: list[Notification] = (
        db.session.query(Notification)
        .filter_by(user_account_id=user_account_id)
        .filter(Notification.dismissed_at.is_(None))  # type: ignore[no-untyped-call]
        .order_by(Notification.last_seen_at.desc())
        .limit(limit)
        .all()
    )
    return appwsrv_schema.GetNotificationsResponse(
        notifications=[serializer.serialize_notification(notification) for notification in notifications],
        unread_count=_unread_count(user_account_id),
    )


@router.post("/mark-read/", operation_id="mark_notifications_read")
def mark_notifications_read(
    user_account_id: int,
    request: appwsrv_schema.MarkNotificationsReadRequest,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.MarkNotificationsReadResponse:
    """Mark notifications as read, or all of them when no ids are given"""
    if user_account_id != current_user_id:
        raise NotAllowedError()
    query = (
        db.session.query(Notification)
        .filter_by(user_account_id=user_account_id)
        .filter(
            Notification.dismissed_at.is_(None),  # type: ignore[no-untyped-call]
            Notification.read_at.is_(None),  # type: ignore[no-untyped-call]
        )
    )
    if request.notification_ids is not None:
        query = query.filter(Notification.id.in_(request.notification_ids))
    now = now_utc()
    notifications = query.all()
    for notification in notifications:
        notification.read_at = now
    _commit_and_publish(user_account_id, EventType.NOTIFICATION_READ if notifications else None)
    return appwsrv_schema.MarkNotificationsReadResponse(unread_count=_unread_count(user_account_id))


@router.post("/{notification_id}/dismiss/", operation_id="dismiss_notification")
def dismiss_notification(
    user_account_id: int,
    notification_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.DismissNotificationResponse:
    """Dismiss a notification.

    Dismissing also closes its aggregation window: should the same problem happen again, it is reported as a
    new notification rather than quietly incrementing this one.
    """
    if user_account_id != current_user_id:
        raise NotAllowedError()
    notification: Notification | None = (
        db.session.query(Notification).filter_by(id=notification_id, user_account_id=user_account_id).one_or_none()
    )
    if notification is None:
        raise ResourceNotFoundError(f"Notification {notification_id} not found")
    changed = notification.dismissed_at is None
    if changed:
        notification.dismissed_at = now_utc()
    _commit_and_publish(user_account_id, EventType.NOTIFICATION_DISMISSED if changed else None)
    return appwsrv_schema.DismissNotificationResponse(unread_count=_unread_count(user_account_id))


@router.post("/dismiss-all/", operation_id="dismiss_all_notifications")
def dismiss_all_notifications(
    user_account_id: int,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.DismissNotificationResponse:
    """Dismiss every notification currently in the panel"""
    if user_account_id != current_user_id:
        raise NotAllowedError()
    now = now_utc()
    notifications: list[Notification] = (
        db.session.query(Notification)
        .filter_by(user_account_id=user_account_id)
        .filter(Notification.dismissed_at.is_(None))  # type: ignore[no-untyped-call]
        .all()
    )
    for notification in notifications:
        notification.dismissed_at = now
    _commit_and_publish(user_account_id, EventType.NOTIFICATION_DISMISSED if notifications else None)
    return appwsrv_schema.DismissNotificationResponse(unread_count=_unread_count(user_account_id))


def _commit_and_publish(user_account_id: int, event_type: str | None) -> None:
    """Commit this request's transaction, publishing a change event in the same commit when given one.

    NOTIFY only fires on COMMIT, so an event must be staged before that commit or it is silently dropped --
    there is no error, no log, nothing to notice later. Routing every mutation through this single function
    (rather than calling `publish` and `db.session.commit()` separately at each call site) means a future
    route added to this file cannot get that ordering backwards by accident.
    """
    if event_type is not None:
        publish(
            db.session,
            Event(
                type=event_type,
                user_account_id=user_account_id,
                seq=int(now_utc().timestamp() * 1000),
            ),
        )
    db.session.commit()
