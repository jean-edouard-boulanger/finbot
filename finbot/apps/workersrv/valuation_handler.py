from finbot.apps.workersrv.schema import ValuationRequest, ValuationResponse
from finbot.model import repository
from finbot.core.serialization import pretty_dump
from finbot.core.db.session import Session
from finbot.core import tracer
from finbot.core.notifier import (
    Notifier,
    CompositeNotifier,
    TwilioNotifier,
    TwilioSettings,
)
from finbot.model import UserAccount
from finbot.clients import SnapClient, HistoryClient

import logging

logger = logging.getLogger()


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


class ValuationHandler(object):
    def __init__(
        self, db_session: Session, snap_client: SnapClient, hist_client: HistoryClient
    ):
        self.db_session = db_session
        self.snap_client = snap_client
        self.hist_client = hist_client

    def handle_valuation(self, request: ValuationRequest) -> ValuationResponse:
        user_account_id = request.user_account_id
        logger.info(
            f"starting workflow for user_id={user_account_id} "
            f"linked_accounts={request.linked_accounts}"
        )

        user_account = repository.get_user_account(self.db_session, user_account_id)
        notifier = _configure_notifier(user_account)

        with tracer.sub_step("snapshot") as step:
            logger.info("taking snapshot")
            snapshot_metadata = self.snap_client.take_snapshot(
                account_id=user_account_id,
                linked_accounts=request.linked_accounts,
                tracer_context=tracer.propagate(),
            )
            step.set_output(snapshot_metadata)

        logger.debug(snapshot_metadata)
        snapshot_id = snapshot_metadata.get("snapshot", {}).get("identifier")
        if snapshot_id is None:
            raise RuntimeError(
                f"missing snapshot_id in snapshot metadata: "
                f"{pretty_dump(snapshot_metadata)}"
            )

        logger.info(f"raw snapshot created with id={snapshot_id}")
        logger.debug(snapshot_metadata)

        with tracer.sub_step("history report") as step:
            logger.info("taking history report")
            step.metadata["snapshot_id"] = snapshot_id
            history_metadata = self.hist_client.write_history(
                snapshot_id, tracer_context=tracer.propagate()
            )
            step.set_output(history_metadata)

        history_entry_id = history_metadata.get("report", {}).get("history_entry_id")
        if history_entry_id is None:
            raise RuntimeError(
                f"missing history_entry_id in history metadata: "
                f"{pretty_dump(history_metadata)}"
            )

        logger.info(
            f"history report written with id={history_entry_id}"
            f" {pretty_dump(history_metadata)}"
        )
        logger.info(f"valuation workflow done for user_id={user_account_id}")

        report = history_metadata["report"]
        with tracer.sub_step("notifications"):
            notifier.notify_valuation(
                valuation=report["user_account_valuation"],
                change_1day=report["valuation_change"]["change_1day"],
                currency=report["valuation_currency"],
            )

        return ValuationResponse.parse_obj(report)
