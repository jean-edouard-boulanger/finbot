from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload
from finbot.clients.finbot import FinbotClient, LineItem
from finbot.core import crypto
from finbot.apps.support import generic_request_handler
from finbot.model import UserAccount
import logging.config
import logging
import os
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


def load_secret(path):
    with open(path) as secret_file:
        return secret_file.read()


secret = load_secret(os.environ["FINBOT_SECRET_PATH"])
db_engine = create_engine(os.environ['FINBOT_DB_URL'])
db_session = scoped_session(sessionmaker(bind=db_engine))
finbot_client = FinbotClient(os.environ.get("FINBOTWSRV_ENDPOINT", "http://127.0.0.1:5001"))

app = Flask(__name__)


@app.teardown_appcontext
def cleanup_context(*args, **kwargs):
    db_session.remove()


@app.route("/snapshot/<user_account_id>", methods=["GET"])
@generic_request_handler
def take_snapshot(user_account_id):
    user_account = (db_session.query(UserAccount)
                              .options(joinedload(UserAccount.external_accounts))
                              .filter_by(id=user_account_id)
                              .first())

    logging.info(f"starting snapshot for user account id '{user_account_id}' "
                 f"linked to {len(user_account.external_accounts)} external accounts")

    raw_snapshot = []
    for account in user_account.external_accounts:
        logging.info(f"taking snapshot for external account id '{account.id}' ({account.provider_id})")
        snapshot_entry = finbot_client.get_financial_data(
            provider=account.provider_id,
            credentials_data=json.loads(crypto.fernet_decrypt(
                account.encrypted_credentials.encode(),
                secret).decode()),
            line_items=[
                LineItem.Balances,
                LineItem.Assets
            ]
        )
        raw_snapshot.append({
            "provider": account.provider_id,
            "account_id": account.id,
            "data": snapshot_entry
        })
    return jsonify({
        "snapshot": raw_snapshot
    })
