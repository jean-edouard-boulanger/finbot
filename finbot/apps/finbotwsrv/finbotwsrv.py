from flask import Flask, jsonify, request
from contextlib import closing
from finbot.providers.factory import get_provider
from finbot.apps.support import (
    generic_request_handler,
    make_error_response,
    make_error
)
import traceback
import logging.config
import logging
import json


logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)',
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


def balances_handler(provider_api):
    return [
        {
            "account": entry["account"],
            "balance": entry["balance"]
        }
        for entry in provider_api.get_balances()["accounts"]
    ]


def assets_handler(provider_api):
    return [
        {
            "account": entry["account"],
            "assets": entry["assets"]
        }
        for entry in provider_api.get_assets()["accounts"]
    ]


def liabilities_handler(provider_api):
    return [
        {
            "account": entry["account"],
            "liabilities": entry["liabilities"]
        }
        for entry in provider_api.get_liabilities()["accounts"]
    ]


def item_handler(item_type, provider_api):
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
        logging.warn(f"error while handling '{item_type}': {e}\n{traceback.format_exc()}")
        return {
            "line_item": item_type,
            "error": make_error(
                user_message=f"failed to retrieve {item_type} line item",
                debug_message=str(e),
                trace=traceback.format_exc()
            )
        }


@app.route("/financial_data", methods=["POST"])
@generic_request_handler
def get_financial_data():
    request_payload = json.loads(request.data)
    provider_id = request_payload["provider"]
    provider = get_provider(request_payload["provider"])
    logging.info(f"initializing provider {provider_id}")
    with closing(provider.api_module.Api()) as provider_api:
        credentials = provider.api_module.Credentials.init(
            request_payload["credentials"])
        try:
            logging.info(f"authenticating {credentials.user_id}")
            provider_api.authenticate(credentials)
        except Exception as e:
            logging.warn(f"authentication failure: {e}")
            return make_error_response(
                user_message="failed to authenticate",
                debug_message=str(e),
                trace=traceback.format_exc()
            )

        return jsonify({
            "financial_data": [
                item_handler(line_item, provider_api)
                for line_item in set(request_payload["items"])
            ]
        })
