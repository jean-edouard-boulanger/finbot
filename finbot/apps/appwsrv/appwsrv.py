from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text, desc
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload, contains_eager
from finbot.apps.support import generic_request_handler, Route
from finbot.core.utils import serialize, pretty_dump
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
import os


logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


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
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


db_engine = create_engine(os.environ['FINBOT_DB_URL'])
db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))

app = Flask(__name__)
CORS(app)


@app.teardown_appcontext
def cleanup_context(*args, **kwargs):
    db_session.remove()


API_V1 = Route("/api/v1")


@app.route(API_V1.providers._, methods=["GET"])
@generic_request_handler
def get_providers():
    providers = db_session.query(Provider).all()
    return jsonify(serialize({
        "providers": [provider for provider in providers]
    }))


ACCOUNT = API_V1.accounts.p("user_account_id")

@app.route(ACCOUNT.history._, methods=["GET"])
@generic_request_handler
def get_user_account_valuation_history(user_account_id):
    history_entries = (db_session.query(UserAccountHistoryEntry)
                                 .filter_by(user_account_id=user_account_id)
                                 .filter_by(available=True)
                                 .order_by(desc(UserAccountHistoryEntry.effective_at))
                                 .options(joinedload(UserAccountHistoryEntry.user_account_valuation_history_entry, innerjoin=True))
                                 .all())

    return jsonify(serialize({
        "historical_valuation": [
                {
                    "date": entry.effective_at,
                    "currency": entry.valuation_ccy,
                    "value": entry.user_account_valuation_history_entry.valuation
                }
                for entry in history_entries
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
                    "date": result.effective_at,
                    "currency": result.valuation_ccy,
                    "value": entry.valuation,
                    "change": entry.valuation_change
                }
            }
            for entry in result.linked_accounts_valuation_history_entries
        ]
    }))


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


