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
