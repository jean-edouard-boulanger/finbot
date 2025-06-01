import logging
import traceback
from typing import Any

from fastapi import FastAPI

from finbot.apps.finbotwsrv import schema
from finbot.apps.http_base import ORJSONResponse, setup_app
from finbot.core import environment
from finbot.core import schema as core_schema
from finbot.core.logging import configure_logging
from finbot.core.schema import ApplicationErrorData, CurrencyCode
from finbot.providers import ProviderBase
from finbot.providers.errors import AuthenticationError
from finbot.providers.factory import get_provider

configure_logging(environment.get_desired_log_level())


app = FastAPI(
    root_path="/api/v1",
    default_response_class=ORJSONResponse,
)
setup_app(app)


def accounts_handler(provider_api: ProviderBase) -> schema.LineItemResults:
    return schema.AccountsResults(results=provider_api.get_accounts())


def assets_handler(provider_api: ProviderBase) -> schema.LineItemResults:
    return schema.AssetsResults(results=provider_api.get_assets().accounts)


def liabilities_handler(provider_api: ProviderBase) -> schema.LineItemResults:
    return schema.LiabilitiesResults(results=provider_api.get_liabilities().accounts)


def item_handler(
    item_type: schema.LineItem,
    provider_api: ProviderBase,
) -> schema.LineItemResults:
    handler = {
        schema.LineItem.Accounts: accounts_handler,
        schema.LineItem.Assets: assets_handler,
        schema.LineItem.Liabilities: liabilities_handler,
    }.get(item_type)
    try:
        if not handler:
            raise ValueError(f"unknown line item: '{item_type}'")
        logging.debug(f"handling '{item_type}' line item")
        return handler(provider_api)
    except Exception as e:
        logging.warning(f"error while handling '{item_type}': {e}\n{traceback.format_exc()}")
        return schema.LineItemError(
            line_item=item_type,
            error=ApplicationErrorData.from_exception(e),
        )


def get_financial_data_impl(
    provider_type: type[ProviderBase],
    authentication_payload: dict[str, Any],
    line_items: list[schema.LineItem],
    user_account_currency: CurrencyCode,
) -> schema.GetFinancialDataResponse:
    with provider_type.create(authentication_payload, user_account_currency) as provider_api:
        provider_api.initialize()
        return schema.GetFinancialDataResponse(
            financial_data=[item_handler(line_item, provider_api) for line_item in set(line_items)]
        )


@app.get("/healthy/")
def healthy() -> core_schema.HealthResponse:
    return core_schema.HealthResponse(healthy=True)


@app.post("/financial_data/")
def get_financial_data(
    json: schema.GetFinancialDataRequest,
) -> schema.GetFinancialDataResponse:
    try:
        provider_type = get_provider(json.provider_id)
        return get_financial_data_impl(
            provider_type=provider_type,
            authentication_payload=json.credentials,
            line_items=json.items,
            user_account_currency=json.user_account_currency,
        )
    except Exception as e:
        return schema.GetFinancialDataResponse(
            financial_data=[],
            error=ApplicationErrorData.from_exception(e),
        )


@app.post("/validate_credentials/")
def validate_credentials(
    json: schema.ValidateCredentialsRequest,
) -> schema.ValidateCredentialsResponse:
    provider_type = get_provider(json.provider_id)
    with provider_type.create(json.credentials, json.user_account_currency) as provider:
        try:
            provider.initialize()
            return schema.ValidateCredentialsResponse(valid=True)
        except AuthenticationError as e:
            return schema.ValidateCredentialsResponse(valid=False, error_message=str(e))
