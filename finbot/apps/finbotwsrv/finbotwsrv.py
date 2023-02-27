from finbot import providers
from finbot.core.db.session import Session
from finbot.core import environment
from finbot.core.logging import configure_logging
from finbot.core.utils import format_stack, configure_stack_printer
from finbot.core.web_service import service_endpoint, ApplicationErrorData
from finbot.providers.factory import get_provider
from finbot.apps.finbotwsrv.schema import FinancialDataRequest, LineItemLiteral

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask import Flask
from flask_pydantic import validate

from typing import Any
import logging


FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)
configure_stack_printer(show_vals=None)

db_engine = create_engine(FINBOT_ENV.database_url)
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))

app = Flask(__name__)


def balances_handler(provider_api: providers.Base) -> list[providers.BalanceEntry]:
    return [
        {"account": entry["account"], "balance": entry["balance"]}
        for entry in provider_api.get_balances()["accounts"]
    ]


def assets_handler(provider_api: providers.Base) -> list[providers.AssetEntry]:
    return [
        {"account": entry["account"], "assets": entry["assets"]}
        for entry in provider_api.get_assets()["accounts"]
    ]


def liabilities_handler(provider_api: providers.Base) -> list[providers.LiabilityEntry]:
    return [
        {"account": entry["account"], "liabilities": entry["liabilities"]}
        for entry in provider_api.get_liabilities()["accounts"]
    ]


def item_handler(item_type: LineItemLiteral, provider_api: providers.Base):
    handler = {
        "balances": balances_handler,
        "assets": assets_handler,
        "liabilities": liabilities_handler,
    }.get(item_type)
    try:
        if not handler:
            raise ValueError(f"unknown line item: '{item_type}'")
        logging.info(f"handling '{item_type}' line item")
        results = handler(provider_api)
        return {"line_item": item_type, "results": results}
    except Exception as e:
        logging.warning(f"error while handling '{item_type}': {e}\n{format_stack()}")
        return {"line_item": item_type, "error": ApplicationErrorData.from_exception(e)}


def get_financial_data_impl(
    provider_type: type[providers.Base],
    authentication_payload: dict[str, Any],
    line_items: list[LineItemLiteral],
):
    with provider_type.create(authentication_payload) as provider_api:
        provider_api.initialize()
        return {
            "financial_data": [
                item_handler(line_item, provider_api) for line_item in set(line_items)
            ]
        }


@app.route("/healthy", methods=["GET"])
@service_endpoint()
def healthy():
    return {"healthy": True}


@app.route("/financial_data", methods=["POST"])
@service_endpoint()
@validate()
def get_financial_data(body: FinancialDataRequest):
    provider = get_provider(body.provider)
    return get_financial_data_impl(provider, body.credentials, body.items)
