from datetime import timedelta

from temporalio import workflow

from finbot.core.temporal_ import TRY_ONCE
from finbot.workflows.fetch_financial_data.schema import (
    GetFinancialDataRequest,
    GetFinancialDataResponse,
    ValidateCredentialsRequest,
    ValidateCredentialsResponse,
)


@workflow.defn(name="validate_credentials")
class ValidateCredentialsWorkflow:
    @workflow.run
    async def run(self, request: ValidateCredentialsRequest) -> ValidateCredentialsResponse:
        from finbot.workflows.fetch_financial_data.activities import validate_credentials

        return await workflow.execute_activity(
            validate_credentials,
            request,
            retry_policy=TRY_ONCE,
            start_to_close_timeout=timedelta(seconds=5.0),
        )


@workflow.defn(name="get_financial_data")
class GetFinancialDataWorkflow:
    @workflow.run
    async def run(self, request: GetFinancialDataRequest) -> GetFinancialDataResponse:
        from finbot.workflows.fetch_financial_data.activities import get_financial_data

        return await workflow.execute_activity(
            get_financial_data,
            request,
            retry_policy=TRY_ONCE,
            start_to_close_timeout=timedelta(minutes=2),
        )
