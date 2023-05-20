import logging

from finbot.core.db.session import Session
from finbot.core.notifier import (
    CompositeNotifier,
    Notifier,
    TwilioNotifier,
    TwilioSettings,
)
from finbot.core.serialization import pretty_dump
from finbot.model import UserAccount, repository
from finbot.services.user_account_snapshot.service import UserAccountSnapshotService
from finbot.services.user_account_valuation.schema import (
    ValuationRequest,
    ValuationResponse,
)
from finbot.services.valuation_history_writer.service import (
    ValuationHistoryWriterService,
)

logger = logging.getLogger(__name__)


def _configure_notifier(user_account: UserAccount) -> Notifier:
    notifiers: list[Notifier] = []
    if user_account.mobile_phone_number and user_account.settings.twilio_settings:
        twilio_settings = TwilioSettings.deserialize(
            user_account.settings.twilio_settings
        )
        notifiers.append(
            TwilioNotifier(twilio_settings, user_account.mobile_phone_number)
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
        logger.info(
            f"starting workflow for user_id={user_account_id} "
            f"linked_accounts={request.linked_accounts}"
        )

        user_account = repository.get_user_account(self._db_session, user_account_id)
        notifier = _configure_notifier(user_account)

        logger.info("taking snapshot")
        snapshot_metadata = self._user_account_snapshot_service.take_snapshot(
            user_account_id=user_account_id,
            linked_account_ids=request.linked_accounts,
        )

        logger.debug(pretty_dump(snapshot_metadata))
        snapshot_id = snapshot_metadata.snapshot.identifier

        logger.info(f"raw snapshot created with id={snapshot_id}")

        logger.info("taking history report")
        history_metadata = self._valuation_history_writer_service.write_history(
            snapshot_id=snapshot_id
        )

        history_report = history_metadata.report

        logger.info(
            f"history report written with id={history_report.history_entry_id}"
            f" {pretty_dump(history_metadata)}"
        )
        logger.info(f"valuation workflow done for user_id={user_account_id}")

        notifier.notify_valuation(
            valuation=history_report.user_account_valuation,
            change_1day=history_report.valuation_change.change_1day,
            currency=history_report.valuation_currency,
        )

        return ValuationResponse(
            history_entry_id=history_report.history_entry_id,
            user_account_valuation=history_report.user_account_valuation,
            valuation_currency=history_report.valuation_currency,
            valuation_date=history_report.valuation_date,
            valuation_change=history_report.valuation_change,
        )
