from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from finbot.workflows.write_valuation_history.schema import WriteHistoryRequest, WriteHistoryResponse


@workflow.defn(name="write_valuation_history")
class WriteValuationHistoryWorkflow:
    @workflow.run
    async def run(self, request: WriteHistoryRequest) -> WriteHistoryResponse:
        from finbot.workflows.write_valuation_history.activities import write_history

        return await workflow.execute_activity(
            write_history,
            request,
            retry_policy=RetryPolicy(
                maximum_attempts=1,
            ),
            start_to_close_timeout=timedelta(seconds=60.0),
        )
