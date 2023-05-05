import logging
from typing import Any

from flask import Flask
from flask_pydantic import validate
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from finbot.apps.finbotwsrv.schema import (
    AssetsResults,
    BalancesResults,
    FinancialDataRequest,
    FinancialDataResponse,
    HealthResponse,
    LiabilitiesResults,
    LineItemError,
    LineItemResults,
    LineItemType,
)
from finbot.core import environment
from finbot.core.db.session import Session
from finbot.core.logging import configure_logging
from finbot.core.utils import configure_stack_printer, format_stack
from finbot.core.web_service import ApplicationErrorData, service_endpoint
from finbot.providers import ProviderBase
from finbot.providers.factory import get_provider

FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)
configure_stack_printer(show_vals=None)

db_engine = create_engine(FINBOT_ENV.database_url)
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))

app = Flask(__name__)


def balances_handler(provider_api: ProviderBase) -> LineItemResults:
    return BalancesResults(results=provider_api.get_balances().accounts)


def assets_handler(provider_api: ProviderBase) -> LineItemResults:
    return AssetsResults(results=provider_api.get_assets().accounts)


def liabilities_handler(provider_api: ProviderBase) -> LineItemResults:
    return LiabilitiesResults(results=provider_api.get_liabilities().accounts)


def item_handler(
    item_type: LineItemType, provider_api: ProviderBase
) -> LineItemResults:
    handler = {
        "balances": balances_handler,
        "assets": assets_handler,
        "liabilities": liabilities_handler,
    }.get(item_type)
    try:
        if not handler:
            raise ValueError(f"unknown line item: '{item_type}'")
        logging.debug(f"handling '{item_type}' line item")
        return handler(provider_api)
    except Exception as e:
        logging.warning(f"error while handling '{item_type}': {e}\n{format_stack()}")
        return LineItemError(
            line_item=item_type, error=ApplicationErrorData.from_exception(e)
        )


def get_financial_data_impl(
    provider_type: type[ProviderBase],
    authentication_payload: dict[str, Any],
    line_items: list[LineItemType],
) -> FinancialDataResponse:
    with provider_type.create(authentication_payload) as provider_api:
        provider_api.initialize()
        return FinancialDataResponse(
            financial_data=[
                item_handler(line_item, provider_api) for line_item in set(line_items)
            ]
        )


@app.route("/healthy/", methods=["GET"])
@service_endpoint()
def healthy() -> HealthResponse:
    return HealthResponse(healthy=True)


@app.route("/financial_data/", methods=["POST"])
@service_endpoint()
@validate()  # type: ignore
def get_financial_data(body: FinancialDataRequest) -> FinancialDataResponse:
    provider = get_provider(body.provider)
    return get_financial_data_impl(provider, body.credentials, body.items)
