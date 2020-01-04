from flask import Flask, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload
from finbot.apps.support import generic_request_handler
from finbot.apps.histwsrv import repository
from finbot.core import dbutils, utils
from finbot.model import (
    UserAccountSnapshot,
    UserAccountHistoryEntry,
    UserAccountValuationHistoryEntry
)
import pandas as pd
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
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


db_engine = create_engine(os.environ['FINBOT_DB_URL'])
db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))

app = Flask(__name__)


def get_user_account_valuation(data: pd.DataFrame):
    return data["value_snapshot_ccy"].sum()


def get_linked_accounts_valuation(data: pd.DataFrame):
    group_by = ["linked_account_snapshot_entry_id", "snapshot_id"]
    return (data.groupby(group_by)["value_snapshot_ccy"]
                .sum()
                .to_dict())


@app.teardown_appcontext
def cleanup_context(*args, **kwargs):
    db_session.remove()


@app.route("/history/<snapshot_id>/create", methods=["GET"])
@generic_request_handler
def create_history(snapshot_id):
    logging.info("fetching snapshot {} metadata".format(snapshot_id))
    snapshot = (db_session.query(UserAccountSnapshot)
                          .filter_by(id=snapshot_id)
                          .first())

    logging.info(f"snapshot is effective at {snapshot.end_time}")
    logging.info(f"fetching consistent snapshot")

    data = repository.get_consistent_snapshot_data(db_session, snapshot_id)
    logging.info(data)

    logging.info(f"consistent snapshot has {len(data)} entries")
    logging.info(f"handling basic valuation")

    user_account_valuation = get_user_account_valuation(data)
    linked_accounts_valuation = get_linked_accounts_valuation(data)
    logging.info(linked_accounts_valuation)

    history_entry = UserAccountHistoryEntry(
        user_account_id=snapshot.user_account_id,
        source_snapshot_id=snapshot_id,
        effective_at=snapshot.end_time,
        currency=snapshot.requested_ccy,
        valuation_history_entry=UserAccountValuationHistoryEntry(
            amount=user_account_valuation
        ))

    db_session.add(history_entry)
    db_session.commit()

    return jsonify({
        "history": {
            "summary": {
                "user_account_valuation": float(user_account_valuation)
            }
        }
    })
