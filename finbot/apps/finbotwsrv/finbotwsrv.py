import logging
import traceback
from typing import Any

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from finbot.apps.finbotwsrv import schema
from finbot.core import environment
from finbot.core import schema as core_schema
from finbot.core.db.session import Session
from finbot.core.logging import configure_logging
from finbot.core.schema import ApplicationErrorData, CurrencyCode
from finbot.core.spec_tree import ResponseSpec, SpecTree
from finbot.core.web_service import CustomJsonProvider, service_endpoint
from finbot.providers import ProviderBase
from finbot.providers.errors import AuthenticationError
from finbot.providers.factory import get_provider

FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)

db_engine = create_engine(FINBOT_ENV.database_url)
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))

app = Flask(__name__)
app.json = CustomJsonProvider(app)  # type: ignore

spec = SpecTree(
    title="Financial data capture service",
    description="API documentation for finbotwsrv",
)


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


@app.route("/healthy/", methods=["GET"])
@service_endpoint()
@spec.validate(resp=ResponseSpec(HTTP_200=core_schema.HealthResponse))
def healthy() -> core_schema.HealthResponse:
    return core_schema.HealthResponse(healthy=True)


@app.route("/financial_data/", methods=["POST"])
@service_endpoint()
@spec.validate(resp=ResponseSpec(HTTP_200=schema.GetFinancialDataResponse))
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


@app.route("/validate_credentials/", methods=["POST"])
@service_endpoint()
@spec.validate(resp=ResponseSpec(HTTP_200=schema.ValidateCredentialsResponse))
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


spec.register(app)
