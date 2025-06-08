from temporalio import activity

from finbot.services.financial_data_fetcher import schema


@activity.defn
async def get_financial_data(request: schema.GetFinancialDataRequest) -> schema.GetFinancialDataResponse:
    from finbot.services.financial_data_fetcher.service import FinancialDataFetcherService

    return await FinancialDataFetcherService().get_financial_data(request)


@activity.defn
async def validate_credentials(
    request: schema.ValidateCredentialsRequest,
) -> schema.ValidateCredentialsResponse:
    from finbot.services.financial_data_fetcher.service import FinancialDataFetcherService

    return await FinancialDataFetcherService().validate_credentials(request)
