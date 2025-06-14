from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from finbot.workflows.fetch_financial_data.schema import ValidateCredentialsRequest, ValidateCredentialsResponse


@workflow.defn(name="validate_credentials")
class ValidateCredentialsWorkflow:
    @workflow.run
    async def run(self, request: ValidateCredentialsRequest) -> ValidateCredentialsResponse:
        from finbot.workflows.fetch_financial_data.activities import validate_credentials

        return await workflow.execute_activity(
            validate_credentials,
            request,
            retry_policy=RetryPolicy(
                maximum_attempts=1,
            ),
            start_to_close_timeout=timedelta(seconds=5.0),
        )
