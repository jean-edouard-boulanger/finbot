from pydantic import BaseModel
from temporalio import activity

from finbot.workflows.write_valuation_history.schema import NewHistoryEntryReport


class SendValuationNotificationActivityRequest(BaseModel):
    user_account_id: int
    report: NewHistoryEntryReport


@activity.defn
def send_valuation_notification(
    request: SendValuationNotificationActivityRequest,
) -> None:
    from finbot.core.notifier import ValuationNotification, configure_notifier
    from finbot.model import ScopedSession, repository

    try:
        with ScopedSession() as session:
            user_account = repository.get_user_account(session, request.user_account_id)
            notifier = configure_notifier(user_account, session)
            notifier.notify_valuation(
                notification=ValuationNotification(
                    user_account_valuation=request.report.user_account_valuation,
                    change_1day=request.report.valuation_change.change_1day,
                    valuation_currency=request.report.valuation_currency,
                )
            )
    except Exception:
        activity.logger.exception("failed to send valuation notification")


class SendErrorNotificationsActivityRequest(BaseModel):
    user_account_id: int
    snapshot_id: int


@activity.defn
def send_error_notifications(
    request: SendErrorNotificationsActivityRequest,
) -> None:
    from finbot.core.notifier import configure_notifier
    from finbot.model import ScopedSession, repository

    try:
        with ScopedSession() as session:
            user_account = repository.get_user_account(session, request.user_account_id)
            notifier = configure_notifier(user_account, session)
            failed_snapshot_entries = repository.find_snapshot_linked_account_errors(
                session,
                request.snapshot_id,
            )
            if failed_snapshot_entries:
                notifier.notify_linked_accounts_snapshot_errors(failed_snapshot_entries)
    except Exception:
        activity.logger.exception("failed to send linked accounts snapshot errors notification")


class SyncLinkedAccountNotificationsActivityRequest(BaseModel):
    user_account_id: int
    snapshot_id: int


class SyncLinkedAccountNotificationsActivityResponse(BaseModel):
    newly_failed_linked_account_ids: list[int] = []
    still_failing_linked_account_ids: list[int] = []
    newly_resolved_linked_account_ids: list[int] = []


@activity.defn
def sync_linked_account_notifications(
    request: SyncLinkedAccountNotificationsActivityRequest,
) -> SyncLinkedAccountNotificationsActivityResponse:
    from finbot.model import ScopedSession
    from finbot.workflows.user_account_valuation import notifications

    try:
        with ScopedSession() as session:
            outcome = notifications.sync_linked_account_notifications(
                session,
                user_account_id=request.user_account_id,
                snapshot_id=request.snapshot_id,
            )
            return SyncLinkedAccountNotificationsActivityResponse(
                newly_failed_linked_account_ids=outcome.newly_failed_linked_account_ids,
                still_failing_linked_account_ids=outcome.still_failing_linked_account_ids,
                newly_resolved_linked_account_ids=outcome.newly_resolved_linked_account_ids,
            )
    except Exception:
        # Notifications are a reporting concern: failing to write one must not fail the valuation itself.
        activity.logger.exception("failed to sync linked account notifications")
        return SyncLinkedAccountNotificationsActivityResponse()


class RaiseValuationFailureNotificationActivityRequest(BaseModel):
    user_account_id: int
    reason: str
    #: The snapshot this run had already created when it failed, if any. See
    #: `notifications.raise_valuation_failure_notification` for why this matters.
    fencing_snapshot_id: int | None = None


@activity.defn
def raise_valuation_failure_notification(
    request: RaiseValuationFailureNotificationActivityRequest,
) -> None:
    from finbot.model import ScopedSession
    from finbot.workflows.user_account_valuation import notifications

    try:
        with ScopedSession() as session:
            notifications.raise_valuation_failure_notification(
                session,
                user_account_id=request.user_account_id,
                reason=request.reason,
                fencing_snapshot_id=request.fencing_snapshot_id,
            )
    except Exception:
        activity.logger.exception("failed to raise valuation failure notification")


class PublishValuationUpdatedEventActivityRequest(BaseModel):
    user_account_id: int
    history_entry_id: int
    snapshot_id: int


@activity.defn
def publish_valuation_updated_event(
    request: PublishValuationUpdatedEventActivityRequest,
) -> None:
    """Tell connected clients the valuation moved, so the dashboard refreshes itself."""
    from finbot.core.events import Event, EventType, publish
    from finbot.model import ScopedSession
    from finbot.workflows.user_account_valuation import notifications

    try:
        with ScopedSession() as session:
            notifications.resolve_valuation_failure_notification(
                session, request.user_account_id, fencing_snapshot_id=request.snapshot_id
            )
            publish(
                session,
                Event(
                    type=EventType.VALUATION_UPDATED,
                    user_account_id=request.user_account_id,
                    seq=request.history_entry_id,
                    data={"history_entry_id": request.history_entry_id},
                ),
            )
            session.commit()
    except Exception:
        activity.logger.exception("failed to publish valuation updated event")


class GetIdsOfUserAccountsThatNeedValuationResponse(BaseModel):
    user_account_ids: list[int]


@activity.defn(name="kickoff_valuation_for_all_user_accounts")
def get_ids_of_user_accounts_that_need_valuation() -> GetIdsOfUserAccountsThatNeedValuationResponse:
    from finbot.model import ScopedSession, UserAccount

    activity.logger.info("Dispatching valuation for all accounts")
    with ScopedSession() as db_session:
        return GetIdsOfUserAccountsThatNeedValuationResponse(
            user_account_ids=[row[0] for row in db_session.query(UserAccount.id).all()]
        )
