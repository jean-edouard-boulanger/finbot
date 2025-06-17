from temporalio import activity

from finbot.workflows.fetch_financial_data import schema


@activity.defn(name="get_financial_data")
async def get_financial_data(
    request: schema.GetFinancialDataRequest,
) -> schema.GetFinancialDataResponse:
    from finbot.workflows.fetch_financial_data.service import FinancialDataFetcherService

    return await FinancialDataFetcherService().get_financial_data(request)


@activity.defn(name="validate_credentials")
async def validate_credentials(
    request: schema.ValidateCredentialsRequest,
) -> schema.ValidateCredentialsResponse:
    from finbot.workflows.fetch_financial_data.service import FinancialDataFetcherService

    return await FinancialDataFetcherService().validate_credentials(request)
