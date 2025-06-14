from fastapi import FastAPI

from finbot._version import __api_version__
from finbot.apps.http_base import ORJSONResponse, setup_app
from finbot.core import environment
from finbot.core import schema as core_schema
from finbot.core.logging import configure_logging
from finbot.workflows.fetch_financial_data import schema
from finbot.workflows.fetch_financial_data.service import FinancialDataFetcherService

configure_logging(environment.get_desired_log_level())


app = FastAPI(
    root_path="/api/v1",
    default_response_class=ORJSONResponse,
    title="Finbot financial data capture service",
    description="API documentation for finbotwsrv",
    version=__api_version__,
    redoc_url="/docs",
    docs_url=None,
)
setup_app(app)


@app.get("/healthy/")
async def healthy() -> core_schema.HealthResponse:
    return core_schema.HealthResponse(healthy=True)


@app.post("/financial_data/")
async def get_financial_data(
    json: schema.GetFinancialDataRequest,
) -> schema.GetFinancialDataResponse:
    return await FinancialDataFetcherService().get_financial_data(json)


@app.post("/validate_credentials/")
async def validate_credentials(
    json: schema.ValidateCredentialsRequest,
) -> schema.ValidateCredentialsResponse:
    return await FinancialDataFetcherService().validate_credentials(json)
