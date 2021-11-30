from finbot import providers
from finbot.core.db.session import Session
from finbot.core import tracer, environment
from finbot.core.logging import configure_logging
from finbot.core.utils import format_stack, configure_stack_printer
from finbot.core.web_service import service_endpoint, ApplicationErrorData
from finbot.providers.factory import get_provider, ProviderDescriptor
from finbot.apps.finbotwsrv.schema import FinancialDataRequest, LineItemLiteral

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask import Flask
from flask_pydantic import validate

from typing import Any
from contextlib import closing
import asyncio
import logging


FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)
configure_stack_printer(show_vals=None)

db_engine = create_engine(FINBOT_ENV.database_url)
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))
tracer.configure(
    identity="finbotwsrv", persistence_layer=tracer.DBPersistenceLayer(db_session)
)

app = Flask(__name__)


@app.before_request
def setup_asyncio_loop():
    """Sets up an asyncio event loop in the current thread if not already setup.
    This is needed for the newer version of undetected-chromedriver.
    This function is run before each request.
    """
    try:
        asyncio.get_event_loop()
        logging.debug("asyncio event loop already setup, skipping")
    except RuntimeError:
        logging.info("setting up asyncio event loop")
        asyncio.set_event_loop(asyncio.new_event_loop())


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
        with tracer.sub_step(f"fetch {item_type}") as step:
            results = handler(provider_api)
            step.set_output(results)
            return {"line_item": item_type, "results": results}
    except Exception as e:
        logging.warning(f"error while handling '{item_type}': {e}\n{format_stack()}")
        return {"line_item": item_type, "error": ApplicationErrorData.from_exception(e)}


def get_financial_data_impl(
    provider_descriptor: ProviderDescriptor,
    credentials: Any,
    line_items: list[LineItemLiteral],
):
    with closing(provider_descriptor.api_module.Api()) as provider_api:
        with tracer.sub_step("authenticate") as step:
            step.metadata["user_id"] = credentials.user_id
            logging.info(f"authenticating {credentials.user_id}")
            provider_api.authenticate(credentials)
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
    credentials = provider.api_module.Credentials.init(body.credentials)
    tracer.current().set_description(body.provider)
    tracer.current().metadata["provider_id"] = body.provider
    tracer.current().metadata["line_items"] = ", ".join(body.items)
    tracer.current().metadata["account"] = body.account_metadata
    return get_financial_data_impl(provider, credentials, body.items)
