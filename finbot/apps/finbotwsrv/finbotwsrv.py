from flask import Flask, jsonify, request
from contextlib import closing
from finbot import providers
from finbot.providers.factory import get_provider
from finbot.providers.errors import AuthFailure
from finbot.apps.support import (
    request_handler,
    make_error_response,
    make_error
)
import stackprinter
import logging.config
import logging


logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s (%(threadName)s) [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


app = Flask(__name__)


def format_stacktrace_for_logs():
    return stackprinter.format(style='darkbg3', show_vals=None)


def format_stacktrace():
    return stackprinter.format(show_vals=None)


def balances_handler(provider_api: providers.Base):
    return [
        {
            "account": entry["account"],
            "balance": entry["balance"]
        }
        for entry in provider_api.get_balances()["accounts"]
    ]


def assets_handler(provider_api: providers.Base):
    return [
        {
            "account": entry["account"],
            "assets": entry["assets"]
        }
        for entry in provider_api.get_assets()["accounts"]
    ]


def liabilities_handler(provider_api: providers.Base):
    return [
        {
            "account": entry["account"],
            "liabilities": entry["liabilities"]
        }
        for entry in provider_api.get_liabilities()["accounts"]
    ]


def item_handler(item_type: str, provider_api: providers.Base):
    handler = {
        "balances": balances_handler,
        "assets": assets_handler,
        "liabilities": liabilities_handler
    }.get(item_type)
    try:
        if not handler:
            raise RuntimeError(f"unknown line item: '{item_type}'")
        logging.info(f"handling '{item_type}' line item")
        return {
            "line_item": item_type,
            "results": handler(provider_api)
        }
    except Exception as e:
        logging.warning(f"error while handling '{item_type}': {e}\n{stackprinter.format()}")
        return {
            "line_item": item_type,
            "error": make_error(
                user_message=f"failed to retrieve {item_type} line item",
                debug_message=str(e),
                trace=stackprinter.format()
            )
        }


@app.route("/financial_data", methods=["POST"])
@request_handler(schema={
    "type": "object",
    "additionalProperties": False,
    "required": ["provider", "credentials", "items"],
    "properties": {
        "provider": {"type": "string"},
        "credentials": {"type": ["null", "object"]},
        "items": {"type": "array", "items": {"type": "string"}}
    }
})
def get_financial_data():
    request_data = request.json
    provider_id = request_data["provider"]
    provider = get_provider(provider_id)
    logging.info(f"initializing provider {provider_id}")
    with closing(provider.api_module.Api()) as provider_api:
        try:
            credentials = provider.api_module.Credentials.init(
                request_data["credentials"])
            logging.info(f"authenticating {credentials.user_id}")
            provider_api.authenticate(credentials)
        except AuthFailure as e:
            logging.warning(f"authentication failure: {e}, trace:\n{format_stacktrace_for_logs()}")
            return make_error_response(
                user_message=str(e),
                debug_message=str(e),
                trace=format_stacktrace())
        except Exception as e:
            logging.warning(f"authentication failure: {e}, trace:\n{format_stacktrace_for_logs()}")
            return make_error_response(
                user_message="authentication failure (unknown error)",
                debug_message=str(e),
                trace=format_stacktrace())

        return jsonify({
            "financial_data": [
                item_handler(line_item, provider_api)
                for line_item in set(request_data["items"])
            ]
        })
