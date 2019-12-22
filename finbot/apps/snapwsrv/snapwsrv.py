from finbot.clients.finbot import FinbotClient, LineItem
from flask import Flask, jsonify, request
from finbot.core import crypto
from finbot.apps.support import (
    generic_request_handler,
    make_error_response,
    make_error
)
import logging.config
import logging
import json
import os


logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s [%(levelname)s] [%(module)s] %(message)s',
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


@app.route("/snapshot", methods=["GET"])
@generic_request_handler
def take_snapshot():
    with open(os.environ["SECRET_PATH"], "rb") as secret_file:
        secret = secret_file.read()
        with open(os.environ["ACCOUNTS_PATH"], "rb") as accounts_file:
            all_accounts_serialized = crypto.fernet_decrypt(
                accounts_file.read(), secret).decode()
            all_accounts = json.loads(all_accounts_serialized)["accounts"]

    logging.info("taking snapshot")
    raw_snapshot = []
    finbot_client = FinbotClient(os.environ.get("FINBOTWSRV_ENDPOINT", "http://127.0.0.1:5001"))
    for account in all_accounts:
        logging.info(f"taking snapshot for account {account['id']} ({account['provider_id']})")
        snapshot_entry = finbot_client.get_financial_data(
            provider=account["provider_id"],
            credentials_data=account["credentials"],
            line_items=[
                LineItem.Balances,
                LineItem.Assets
            ]
        )
        raw_snapshot.append({
            "provider": account["provider_id"],
            "account_id": account["id"],
            "data": snapshot_entry
        })
    return jsonify({
        "snapshot": raw_snapshot
    })
