from datetime import timedelta

from temporalio import workflow

from finbot.services.financial_data_fetcher.schema import ValidateCredentialsRequest, ValidateCredentialsResponse


@workflow.defn
class ValidateCredentialsWorkflow:
    @workflow.run
    async def run(self, request: ValidateCredentialsRequest) -> ValidateCredentialsResponse:
        from finbot.services.financial_data_fetcher.activities import validate_credentials

        return await workflow.execute_activity(
            validate_credentials,
            request,
            start_to_close_timeout=timedelta(seconds=15),
        )
