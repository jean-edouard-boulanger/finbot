import asyncio
from datetime import timedelta

from temporalio import workflow

from finbot.core.schema import ApplicationErrorData
from finbot.core.temporal_ import TRY_ONCE
from finbot.workflows.user_account_snapshot.schema import (
    LinkedAccountSnapshotRequest,
    LinkedAccountSnapshotResponse,
    SnapshotMetadata,
    TakeRawSnapshotRequest,
    TakeRawSnapshotResponse,
    TakeSnapshotRequest,
    TakeSnapshotResponse,
)


@workflow.defn(name="take_user_account_raw_snapshot")
class TakeUserAccountRawSnapshotWorkflow:
    @workflow.run
    async def run(
        self,
        request: TakeRawSnapshotRequest,
    ) -> TakeRawSnapshotResponse:
        from finbot.workflows.user_account_snapshot.activities import prepare_raw_snapshot_requests

        requests = await workflow.execute_activity(
            prepare_raw_snapshot_requests,
            request,
            retry_policy=TRY_ONCE,
            start_to_close_timeout=timedelta(seconds=5.0),
        )
        results: list[LinkedAccountSnapshotResponse] = await asyncio.gather(
            *[self.snapshot_linked_account(request) for request in requests]
        )
        return TakeRawSnapshotResponse(entries=results)

    @classmethod
    async def snapshot_linked_account(cls, request: LinkedAccountSnapshotRequest) -> LinkedAccountSnapshotResponse:
        from finbot.workflows.fetch_financial_data.activities import get_financial_data
        from finbot.workflows.fetch_financial_data.schema import GetFinancialDataRequest

        try:
            await workflow.execute_activity(
                get_financial_data,
                GetFinancialDataRequest(
                    provider_id=request.provider_id,
                    encrypted_credentials=request.encrypted_credentials,
                    items=request.line_items,
                    user_account_currency=request.user_account_currency,
                ),
                retry_policy=TRY_ONCE,
                start_to_close_timeout=request.timeout,
            )
        except Exception as e:
            workflow.logger.exception(f"Failed to take snapshot of account {request.linked_account_id}")
            return LinkedAccountSnapshotResponse(request=request, snapshot_data=ApplicationErrorData.from_exception(e))

        return LinkedAccountSnapshotResponse(
            request=request,
            # TODO: implement retries
            snapshot_data=await workflow.execute_activity(
                get_financial_data,
                GetFinancialDataRequest(
                    provider_id=request.provider_id,
                    encrypted_credentials=request.encrypted_credentials,
                    items=request.line_items,
                    user_account_currency=request.user_account_currency,
                ),
                retry_policy=TRY_ONCE,
                start_to_close_timeout=request.timeout,
            ),
        )


@workflow.defn(name="take_user_account_snapshot")
class TakeUserAccountSnapshotWorkflow:
    @workflow.run
    async def run(
        self,
        request: TakeSnapshotRequest,
    ) -> TakeSnapshotResponse:
        from finbot.workflows.user_account_snapshot.activities import (
            BuildAndPersistFinalSnapshotActivityRequest,
            build_and_persist_final_snapshot,
            create_empty_snapshot,
        )

        new_snapshot_meta: SnapshotMetadata = await workflow.execute_activity(
            create_empty_snapshot,
            request.user_account_id,
            retry_policy=TRY_ONCE,
            start_to_close_timeout=timedelta(seconds=10.0),
        )
        raw_snapshot: TakeRawSnapshotResponse = await workflow.execute_child_workflow(
            TakeUserAccountRawSnapshotWorkflow.run,
            TakeRawSnapshotRequest(
                user_account_id=request.user_account_id,
                linked_account_ids=request.linked_account_ids,
            ),
            retry_policy=TRY_ONCE,
            task_timeout=request.timeout,
        )
        return TakeSnapshotResponse(
            snapshot=await workflow.execute_activity(
                build_and_persist_final_snapshot,
                BuildAndPersistFinalSnapshotActivityRequest(
                    snapshot_meta=new_snapshot_meta,
                    raw_snapshot=raw_snapshot.entries,
                ),
                retry_policy=TRY_ONCE,
                start_to_close_timeout=timedelta(seconds=60.0),
            )
        )
