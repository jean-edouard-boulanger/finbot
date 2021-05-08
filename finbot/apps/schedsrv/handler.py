from finbot.apps.schedsrv.errors import WorkflowError
from finbot.core.notifier import (
    Notifier,
    CompositeNotifier,
    TwilioNotifier,
    TwilioSettings,
)
from finbot.model import UserAccount
from finbot.clients import sched as sched_client
from finbot.clients import SnapClient, HistoryClient
from finbot.core import utils, tracer

import logging


def get_user_account(db_session, user_account_id: int) -> UserAccount:
    account = db_session.query(UserAccount).filter_by(id=user_account_id).one()
    if not account:
        raise RuntimeError(f"user account not found: {user_account_id}")
    return account


def configure_notifier(user_account: UserAccount) -> Notifier:
    notifiers: list[Notifier] = []
    if user_account.mobile_phone_number and user_account.settings.twilio_settings:
        twilio_settings = TwilioSettings.deserialize(
            user_account.settings.twilio_settings
        )
        notifiers.append(
            TwilioNotifier(twilio_settings, user_account.mobile_phone_number)
        )
    return CompositeNotifier(notifiers)


class RequestHandler(object):
    def __init__(self, snap_client: SnapClient, hist_client: HistoryClient, db_session):
        self.snap_client = snap_client
        self.hist_client = hist_client
        self.db_session = db_session

    def _run_workflow(self, valuation_request: sched_client.TriggerValuationRequest):
        user_account_id = valuation_request.user_account_id
        logging.info(f"starting workflow for user_id={user_account_id}")

        user_account = get_user_account(self.db_session, user_account_id)
        notifier = configure_notifier(user_account)

        with tracer.sub_step("snapshot") as step:
            logging.info("taking snapshot")
            snapshot_metadata = self.snap_client.take_snapshot(
                account_id=user_account_id,
                linked_accounts=valuation_request.linked_accounts,
                tracer_context=tracer.propagate(),
            )
            step.set_output(snapshot_metadata)

        logging.debug(snapshot_metadata)
        snapshot_id = snapshot_metadata.get("snapshot", {}).get("identifier")
        if snapshot_id is None:
            raise WorkflowError(
                f"missing snapshot_id in snapshot metadata: "
                f"{utils.pretty_dump(snapshot_metadata)}"
            )

        logging.info(f"raw snapshot created with id={snapshot_id}")
        logging.debug(snapshot_metadata)

        with tracer.sub_step("history report") as step:
            logging.info("taking history report")
            step.metadata["snapshot_id"] = snapshot_id
            history_metadata = self.hist_client.write_history(
                snapshot_id, tracer_context=tracer.propagate()
            )
            step.set_output(history_metadata)

        history_entry_id = history_metadata.get("report", {}).get("history_entry_id")
        if history_entry_id is None:
            raise WorkflowError(
                f"missing history_entry_id in history metadata: "
                f"{utils.pretty_dump(history_metadata)}"
            )

        logging.info(
            f"history report written with id={history_entry_id}"
            f" {utils.pretty_dump(history_metadata)}"
        )
        logging.info(f"valuation workflow done for user_id={user_account_id}")

        with tracer.sub_step("notifications"):
            report = history_metadata["report"]
            notifier.notify_valuation(
                valuation=report["user_account_valuation"],
                change_1day=report["valuation_change"]["change_1day"],
                currency=report["valuation_currency"],
            )

    def handle_valuation(self, valuation_request: sched_client.TriggerValuationRequest):
        with tracer.root("valuation") as step:
            step.metadata["request"] = sched_client.serialize(valuation_request)
            self._run_workflow(valuation_request)
