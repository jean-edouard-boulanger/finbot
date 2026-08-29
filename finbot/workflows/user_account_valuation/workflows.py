import asyncio
from datetime import timedelta

from temporalio import workflow

from finbot.core.temporal_ import TRY_ONCE
from finbot.workflows.user_account_snapshot.schema import TakeSnapshotRequest
from finbot.workflows.user_account_snapshot.workflows import TakeUserAccountSnapshotWorkflow
from finbot.workflows.user_account_valuation.schema import ValuationRequest, ValuationResponse
from finbot.workflows.write_valuation_history.schema import WriteHistoryRequest, WriteHistoryResponse
from finbot.workflows.write_valuation_history.workflows import WriteValuationHistoryWorkflow


@workflow.defn(name="user_account_valuation")
class UserAccountValuationWorkflow:
    @workflow.run
    async def run(
        self,
        request: ValuationRequest,
    ) -> ValuationResponse:
        from finbot.core.serialization import pretty_dump
        from finbot.workflows.user_account_valuation.activities import (
            PublishValuationUpdatedEventActivityRequest,
            RaiseValuationFailureNotificationActivityRequest,
            SendErrorNotificationsActivityRequest,
            SendValuationNotificationActivityRequest,
            SyncLinkedAccountNotificationsActivityRequest,
            publish_valuation_updated_event,
            raise_valuation_failure_notification,
            send_error_notifications,
            send_valuation_notification,
            sync_linked_account_notifications,
        )

        workflow.logger.info(
            f"starting workflow for user_id={request.user_account_id} linked_accounts={request.linked_accounts}"
        )
        # `snapshot_id` is filled in as soon as the snapshot step succeeds and used to fence any failure
        # notification raised below: without it, a failure here could otherwise be reported using a stale or
        # out-of-order identity against a concurrent run for the same account. A failure before this point
        # has no snapshot to fence with, which is an inherent gap for a run that never got that far.
        snapshot_id: int | None = None
        try:
            workflow.logger.info("taking snapshot")
            snapshot_metadata = await workflow.execute_child_workflow(
                TakeUserAccountSnapshotWorkflow.run,
                TakeSnapshotRequest(
                    user_account_id=request.user_account_id,
                    linked_account_ids=request.linked_accounts,
                ),
                retry_policy=TRY_ONCE,
            )
            snapshot_id = snapshot_metadata.snapshot.identifier
            workflow.logger.info(f"raw snapshot created with id={snapshot_id}")
            # Runs before the history child, which is TRY_ONCE and can fail: a history-writing problem must
            # not suppress provider failures we already know about.
            await workflow.execute_activity(
                sync_linked_account_notifications,
                SyncLinkedAccountNotificationsActivityRequest(
                    user_account_id=request.user_account_id,
                    snapshot_id=snapshot_id,
                ),
                retry_policy=TRY_ONCE,
                start_to_close_timeout=timedelta(seconds=60),
            )
            workflow.logger.info("writing history report")
            history_metadata: WriteHistoryResponse = await workflow.execute_child_workflow(
                WriteValuationHistoryWorkflow.run,
                WriteHistoryRequest(
                    snapshot_id=snapshot_id,
                ),
                retry_policy=TRY_ONCE,
            )
            history_report = history_metadata.report
            workflow.logger.info(
                f"history report written with id={history_report.history_entry_id} {pretty_dump(history_metadata)}"
            )
            workflow.logger.info(f"valuation workflow done for user_id={request.user_account_id}")
            if request.notify_valuation:
                await workflow.execute_activity(
                    send_valuation_notification,
                    SendValuationNotificationActivityRequest(
                        user_account_id=request.user_account_id,
                        report=history_report,
                    ),
                    retry_policy=TRY_ONCE,
                    start_to_close_timeout=timedelta(seconds=60),
                )
            await workflow.execute_activity(
                send_error_notifications,
                SendErrorNotificationsActivityRequest(
                    user_account_id=request.user_account_id,
                    snapshot_id=snapshot_id,
                ),
                retry_policy=TRY_ONCE,
                start_to_close_timeout=timedelta(seconds=60),
            )
            await workflow.execute_activity(
                publish_valuation_updated_event,
                PublishValuationUpdatedEventActivityRequest(
                    user_account_id=request.user_account_id,
                    history_entry_id=history_report.history_entry_id,
                    snapshot_id=snapshot_id,
                ),
                retry_policy=TRY_ONCE,
                start_to_close_timeout=timedelta(seconds=60),
            )
        except Exception as e:
            # RunValuationForAllUsers swallows per-user failures, so without this the user gets no signal at
            # all: the dashboard would simply stop moving with nothing to explain why. Covers the whole run,
            # not just the snapshot step, so a failure while writing history or publishing still surfaces.
            await workflow.execute_activity(
                raise_valuation_failure_notification,
                RaiseValuationFailureNotificationActivityRequest(
                    user_account_id=request.user_account_id,
                    reason=f"{e}",
                    fencing_snapshot_id=snapshot_id,
                ),
                retry_policy=TRY_ONCE,
                start_to_close_timeout=timedelta(seconds=60),
            )
            raise
        return ValuationResponse(
            history_entry_id=history_report.history_entry_id,
            user_account_valuation=history_report.user_account_valuation,
            valuation_currency=history_report.valuation_currency,
            valuation_date=history_report.valuation_date,
            valuation_change=history_report.valuation_change,
        )


@workflow.defn(name="run_valuation_for_all_users")
class RunValuationForAllUsers:
    @workflow.run
    async def run(self) -> None:
        from finbot.workflows.user_account_valuation.activities import (
            GetIdsOfUserAccountsThatNeedValuationResponse,
            get_ids_of_user_accounts_that_need_valuation,
        )

        result: GetIdsOfUserAccountsThatNeedValuationResponse = await workflow.execute_activity(
            get_ids_of_user_accounts_that_need_valuation,
            retry_policy=TRY_ONCE,
            start_to_close_timeout=timedelta(seconds=60.0),
        )
        workflow.logger.info(f"kicking off valuation for all ({len(result.user_account_ids)}) users")
        valuation_tasks = [
            workflow.execute_child_workflow(
                UserAccountValuationWorkflow.run,
                ValuationRequest(
                    user_account_id=user_account_id,
                ),
                retry_policy=TRY_ONCE,
            )
            for user_account_id in result.user_account_ids
        ]
        for user_account_id, valuation_result_coro in zip(
            result.user_account_ids, asyncio.as_completed(valuation_tasks)
        ):
            try:
                await valuation_result_coro
            except Exception:
                workflow.logger.exception(f"Valuation workflow failed for user account {user_account_id}")
            else:
                workflow.logger.info(f"Valuation workflow complete for user account {user_account_id}")
