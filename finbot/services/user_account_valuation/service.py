import logging

from finbot import model
from finbot.core.db.session import Session
from finbot.core.email_delivery import DeliverySettings as EmailDeliverySettings
from finbot.core.environment import get_twilio_environment, is_twilio_configured
from finbot.core.kv_store import DBKVStore
from finbot.core.notifier import (
    CompositeNotifier,
    EmailNotifier,
    Notifier,
    TwilioNotifier,
    TwilioSettings,
    ValuationNotification,
)
from finbot.core.serialization import pretty_dump
from finbot.core.utils import some
from finbot.model import repository
from finbot.services.user_account_snapshot.service import UserAccountSnapshotService
from finbot.services.user_account_valuation.schema import (
    ValuationRequest,
    ValuationResponse,
)
from finbot.services.valuation_history_writer.service import (
    ValuationHistoryWriterService,
)

logger = logging.getLogger(__name__)


def _configure_notifier(db_session: Session, user_account: model.UserAccount) -> Notifier:
    notifiers: list[Notifier] = []
    if user_account.mobile_phone_number and is_twilio_configured():
        twilio_settings = TwilioSettings.from_env(some(get_twilio_environment()))
        notifiers.append(
            TwilioNotifier(
                twilio_settings=twilio_settings,
                recipient_phone_number=user_account.mobile_phone_number,
            )
        )
    kv_store = DBKVStore(db_session)
    email_delivery_settings = kv_store.get_entity(EmailDeliverySettings)
    if email_delivery_settings:
        notifiers.append(
            EmailNotifier(
                email_delivery_settings=email_delivery_settings,
                recipient_email=user_account.email,
            )
        )
    return CompositeNotifier(notifiers)


class UserAccountValuationService(object):
    def __init__(
        self,
        db_session: Session,
        user_account_snapshot_service: UserAccountSnapshotService,
        valuation_history_writer_service: ValuationHistoryWriterService,
    ):
        self._db_session = db_session
        self._user_account_snapshot_service = user_account_snapshot_service
        self._valuation_history_writer_service = valuation_history_writer_service

    def process_valuation(self, request: ValuationRequest) -> ValuationResponse:
        user_account_id = request.user_account_id
        logger.info(f"starting workflow for user_id={user_account_id} " f"linked_accounts={request.linked_accounts}")

        user_account = repository.get_user_account(self._db_session, user_account_id)
        notifier = _configure_notifier(db_session=self._db_session, user_account=user_account)

        logger.info("taking snapshot")
        snapshot_metadata = self._user_account_snapshot_service.take_snapshot(
            user_account_id=user_account_id,
            linked_account_ids=request.linked_accounts,
        )

        logger.debug(pretty_dump(snapshot_metadata))
        snapshot_id = snapshot_metadata.snapshot.identifier

        logger.info(f"raw snapshot created with id={snapshot_id}")

        logger.info("taking history report")
        history_metadata = self._valuation_history_writer_service.write_history(snapshot_id=snapshot_id)

        history_report = history_metadata.report

        logger.info(
            f"history report written with id={history_report.history_entry_id}" f" {pretty_dump(history_metadata)}"
        )
        logger.info(f"valuation workflow done for user_id={user_account_id}")

        if request.notify_valuation:
            try:
                notifier.notify_valuation(
                    notification=ValuationNotification(
                        user_account_valuation=history_report.user_account_valuation,
                        change_1day=history_report.valuation_change.change_1day,
                        valuation_currency=history_report.valuation_currency,
                    )
                )
            except Exception as e:
                logger.warning("failed to send valuation notification: %s", e)

        try:
            failed_snapshot_entries = repository.find_snapshot_linked_account_errors(
                session=self._db_session, snapshot_id=snapshot_id
            )
            if failed_snapshot_entries:
                notifier.notify_linked_accounts_snapshot_errors(failed_snapshot_entries)
        except Exception as e:
            logger.warning("failed to send linked accounts snapshot errors notification: %s", e)

        return ValuationResponse(
            history_entry_id=history_report.history_entry_id,
            user_account_valuation=history_report.user_account_valuation,
            valuation_currency=history_report.valuation_currency,
            valuation_date=history_report.valuation_date,
            valuation_change=history_report.valuation_change,
        )
