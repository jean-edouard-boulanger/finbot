from datetime import timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text, desc, asc
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload, contains_eager
from finbot.clients.finbot import FinbotClient
from finbot.apps.appwsrv import timeseries
from finbot.apps.support import generic_request_handler, Route
from finbot.core.utils import serialize, pretty_dump
from finbot.core import crypto
from finbot.core import dbutils
from finbot.model import (
    Provider,
    UserAccount,
    LinkedAccount,
    UserAccountSnapshot,
    UserAccountHistoryEntry,
    UserAccountValuationHistoryEntry,
    LinkedAccountValuationHistoryEntry,
    SubAccountValuationHistoryEntry,
    SubAccountItemValuationHistoryEntry,
)
import logging.config
import logging
import itertools
import json
import os


#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


SECRET = open(os.environ["FINBOT_SECRET_PATH"], "r").read()
FINBOT_FINBOTWSRV_ENDPOINT = os.environ["FINBOT_FINBOTWSRV_ENDPOINT"]


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
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


db_engine = create_engine(os.environ['FINBOT_DB_URL'])
db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))


app = Flask(__name__)
CORS(app)


class ApplicationError(RuntimeError):
    pass


@app.teardown_appcontext
def cleanup_context(*args, **kwargs):
    db_session.remove()


API_V1 = Route("/api/v1")


@app.route(API_V1.providers._, methods=["POST"])
@generic_request_handler
def create_provider():
    data = request.json
    with db_session.persist(Provider()) as provider:
        provider.id = data["id"]
        provider.description = data["description"]
        provider.website_url = data["website_url"]
        provider.credentials_schema = data["credentials_schema"]
    return jsonify(provider.serialize())


@app.route(API_V1.providers._, methods=["GET"])
@generic_request_handler
def get_providers():
    providers = db_session.query(Provider).all()
    return jsonify(serialize({
        "providers": [provider for provider in providers]
    }))


@app.route(API_V1.providers.p("provider_id")._, methods=["DELETE"])
@generic_request_handler
def delete_provider(provider_id):
    count = db_session.query(Provider).filter_by(id=provider_id).delete()
    db_session.commit()
    logging.info(f"deleted provider_id={provider_id}")
    return jsonify({"deleted": count})


ACCOUNT = API_V1.accounts.p("user_account_id")


@app.route(ACCOUNT.history._, methods=["GET"])
@generic_request_handler
def get_user_account_valuation_history(user_account_id):
    history_entries = (db_session.query(UserAccountHistoryEntry)
                                 .filter_by(user_account_id=user_account_id)
                                 .filter_by(available=True)
                                 .order_by(asc(UserAccountHistoryEntry.effective_at))
                                 .options(joinedload(UserAccountHistoryEntry.user_account_valuation_history_entry, innerjoin=True))
                                 .all())

    return jsonify(serialize({
        "historical_valuation": [
                {
                    "date": entry.effective_at,
                    "currency": entry.valuation_ccy,
                    "value": entry.user_account_valuation_history_entry.valuation
                }
                for entry in timeseries.sample_time_series(
                    history_entries,
                    time_getter=(lambda item: item.effective_at),
                    frequency=timedelta(days=1))
        ]
    }))


@app.route(ACCOUNT._, methods=["GET"])
@generic_request_handler
def get_account_valuation(user_account_id):
    entry = (db_session.query(UserAccountHistoryEntry)
                       .filter_by(user_account_id=user_account_id)
                       .filter_by(available=True)
                       .order_by(desc(UserAccountHistoryEntry.effective_at))
                       .options(joinedload(UserAccountHistoryEntry.user_account_valuation_history_entry))
                       .options(joinedload(UserAccountHistoryEntry.user_account))
                       .options(joinedload(UserAccountHistoryEntry.user_account, UserAccount.settings))
                       .first())

    if entry is None:
        raise ApplicationError(f"user account {user_account_id} not found")

    account = entry.user_account
    return jsonify(serialize({
        "result": {
            "user_account": {
                "id": account.id,
                "email": account.email,
                "full_name": account.full_name,
                "settings": {
                    "valuation_ccy": account.settings.valuation_ccy,
                    "created_at": account.settings.created_at,
                    "updated_at": account.settings.updated_at
                },
                "created_at": account.created_at,
                "updated_at": account.updated_at
            },
            "valuation": {
                "history_entry_id": entry.id,
                "date": entry.effective_at,
                "currency": entry.valuation_ccy,
                "value": entry.user_account_valuation_history_entry.valuation,
                "total_liabilities": entry.user_account_valuation_history_entry.total_liabilities,
                "change": entry.user_account_valuation_history_entry.valuation_change
            }
        }
    }))


@app.route(ACCOUNT.linked_accounts._, methods=["GET"])
@generic_request_handler
def get_linked_accounts_valuation(user_account_id):
    result = (db_session.query(UserAccountHistoryEntry)
                        .filter_by(user_account_id=user_account_id)
                        .filter_by(available=True)
                        .order_by(desc(UserAccountHistoryEntry.effective_at))
                        .options(joinedload(UserAccountHistoryEntry.linked_accounts_valuation_history_entries))
                        .options(
                            joinedload(
                                UserAccountHistoryEntry.linked_accounts_valuation_history_entries,
                                LinkedAccountValuationHistoryEntry.valuation_change)
                        )
                        .options(
                            joinedload(
                                UserAccountHistoryEntry.linked_accounts_valuation_history_entries,
                                LinkedAccountValuationHistoryEntry.linked_account)
                        )
                        .options(
                            joinedload(
                                UserAccountHistoryEntry.linked_accounts_valuation_history_entries,
                                LinkedAccountValuationHistoryEntry.effective_snapshot)
                        )
                        .first())

    return jsonify(serialize({
        "linked_accounts": [
            {
                "linked_account": {
                    "id": entry.linked_account.id,
                    "provider_id": entry.linked_account.provider_id,
                    "description": entry.linked_account.account_name,
                },
                "valuation": {
                    "date": entry.effective_snapshot.effective_at,
                    "currency": result.valuation_ccy,
                    "value": entry.valuation,
                    "change": entry.valuation_change
                }
            }
            for entry in result.linked_accounts_valuation_history_entries
        ]
    }))


@app.route(ACCOUNT.linked_accounts._, methods=["POST"])
@generic_request_handler
def link_to_external_account(user_account_id):
    user_account = (db_session.query(UserAccount)
                              .filter_by(id=user_account_id)
                              .first())
    if not user_account:
        raise ApplicationError(f"could not find user account with id {user_account_id}")

    data = request.get_json()
    finbot_client = FinbotClient(FINBOT_FINBOTWSRV_ENDPOINT)

    provider_id = data["provider_id"]
    logging.info(f"validating authentication details for account {user_account_id} and provider {provider_id}")

    finbot_response = finbot_client.get_financial_data(
        provider=provider_id,
        credentials_data=data["credentials"],
        line_items=[])

    if "error" in finbot_response:
        user_message = finbot_response["error"]["user_message"]
        raise ApplicationError(f"unable to validate provided credentials: {user_message}")

    with db_session.persist(user_account):
        user_account.linked_accounts.append(
            LinkedAccount(
                provider_id=data["provider_id"],
                account_name=data["account_name"],
                encrypted_credentials=crypto.fernet_encrypt(
                    json.dumps(data["credentials"]).encode(), SECRET).decode()))


LINKED_ACCOUNT = ACCOUNT.linked_accounts.p("linked_account_id")


@app.route(LINKED_ACCOUNT.history._, methods=["GET"])
@generic_request_handler
def get_linked_account_historical_valuation(user_account_id, linked_account_id):
    linked_account_id = int(linked_account_id)
    results = (db_session.query(UserAccountHistoryEntry)
                         .filter_by(user_account_id=user_account_id)
                         .filter_by(available=True)
                         .join(UserAccountHistoryEntry.linked_accounts_valuation_history_entries)
                         .options(
                             contains_eager(UserAccountHistoryEntry.linked_accounts_valuation_history_entries))
                         .filter(LinkedAccountValuationHistoryEntry.linked_account_id == linked_account_id)
                         .order_by(desc(UserAccountHistoryEntry.effective_at))
                         .all())

    output_entries = []
    for account_entry in results:
        assert len(account_entry.linked_accounts_valuation_history_entries) == 1
        for entry in account_entry.linked_accounts_valuation_history_entries:
            assert entry.linked_account_id == linked_account_id
            output_entries.append({
                    "linked_account_id": entry.linked_account_id,
                    "date": account_entry.effective_at,
                    "currency": account_entry.valuation_ccy,
                    "value": entry.valuation
                })
    return jsonify(serialize(output_entries))
