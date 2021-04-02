from typing import Dict
from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from finbot.apps.support import request_handler
from finbot.apps.histwsrv import repository
from finbot.core.utils import serialize, pretty_dump, configure_logging
from finbot.core import dbutils, tracer, environment
from finbot.model import (
    UserAccountSnapshot,
    UserAccountHistoryEntry,
    UserAccountValuationHistoryEntry,
    LinkedAccountValuationHistoryEntry,
    SubAccountValuationHistoryEntry,
    SubAccountItemValuationHistoryEntry,
)
import pandas as pd
import logging


configure_logging()


FINBOT_ENV = environment.get()
db_engine = create_engine(FINBOT_ENV.database_url)
db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))
tracer.configure(
    identity="hitwsrv", persistence_layer=tracer.DBPersistenceLayer(db_session)
)

app = Flask(__name__)


def get_user_account_valuation(data: pd.DataFrame) -> float:
    return data["value_snapshot_ccy"].sum()


def get_user_account_liabilities(data: pd.DataFrame) -> float:
    return data.loc[data["value_snapshot_ccy"] < 0, "value_snapshot_ccy"].sum()


def get_linked_accounts_valuation(data: pd.DataFrame) -> Dict:
    groups = ["linked_account_id", "snapshot_id"]
    return data.groupby(groups)["value_snapshot_ccy"].sum().to_dict()


def get_sub_accounts_valuation(data: pd.DataFrame):
    groups = [
        "linked_account_id",
        "sub_account_id",
        "sub_account_ccy",
        "sub_account_description",
        "sub_account_type",
    ]
    data = (
        data.groupby(groups)
        .agg({"value_sub_account_ccy": "sum", "value_snapshot_ccy": "sum"})
        .to_dict()
    )
    sub_account_data = data["value_sub_account_ccy"]
    snapshot_data = data["value_snapshot_ccy"]
    return {
        path: (value, sub_account_data[path]) for path, value in snapshot_data.items()
    }


def iter_sub_accounts_valuation_history_entries(data: pd.DataFrame):
    for _, row in data.iterrows():
        yield SubAccountItemValuationHistoryEntry(
            linked_account_id=row["linked_account_id"],
            sub_account_id=row["sub_account_id"],
            item_type=row["item_type"],
            name=row["item_name"],
            item_subtype=row["item_subtype"],
            units=row["item_units"],
            valuation=row["value_snapshot_ccy"],
            valuation_sub_account_ccy=row["value_sub_account_ccy"],
        )


@app.teardown_appcontext
def cleanup_context(*args, **kwargs):
    db_session.remove()


@app.route("/healthy", methods=["GET"])
@request_handler()
def healthy():
    return jsonify({"healthy": True})


@app.route("/history/<snapshot_id>/write", methods=["POST"])
@request_handler()
def write_history(snapshot_id):
    repo = repository.ReportRepository(db_session)

    logging.info("fetching snapshot_id={} metadata".format(snapshot_id))
    snapshot = db_session.query(UserAccountSnapshot).filter_by(id=snapshot_id).first()

    valuation_date = snapshot.end_time
    logging.info(f"snapshot is effective_at={valuation_date}")
    logging.info("fetching consistent snapshot")

    with tracer.sub_step("get consistent snapshot") as step:
        snapshot_data = repo.get_consistent_snapshot_data(snapshot_id)
        step.set_output(snapshot_data.to_csv())

    logging.debug(snapshot_data.to_csv())

    logging.info(f"consistent snapshot has entries={len(snapshot_data)}")
    logging.info("creating new history entry (marked not available)")

    with db_session.persist(UserAccountHistoryEntry()) as history_entry:
        history_entry.user_account_id = snapshot.user_account_id
        history_entry.source_snapshot_id = snapshot_id
        history_entry.effective_at = valuation_date
        history_entry.valuation_ccy = snapshot.requested_ccy
        history_entry.user_account_id = snapshot.user_account_id
        history_entry.available = False

    logging.info(f"blank history entry created with id={history_entry.id}")

    logging.info("handling basic valuation")

    user_account_valuation = get_user_account_valuation(snapshot_data)
    logging.info(f"user account valuation {user_account_valuation}")

    user_account_total_liabilities = get_user_account_liabilities(snapshot_data)
    logging.info(f"user account liabilities {user_account_total_liabilities}")

    with db_session.persist(history_entry):
        history_entry.user_account_valuation_history_entry = (
            UserAccountValuationHistoryEntry(
                valuation=user_account_valuation,
                total_liabilities=user_account_total_liabilities,
            )
        )

    linked_accounts_valuation = get_linked_accounts_valuation(snapshot_data)
    logging.info("fetched linked accounts valuation")
    logging.debug(pretty_dump(linked_accounts_valuation))

    with db_session.persist(history_entry):
        history_entry.linked_accounts_valuation_history_entries.extend(
            [
                LinkedAccountValuationHistoryEntry(
                    linked_account_id=linked_account_id,
                    effective_snapshot_id=effective_snapshot_id,
                    valuation=valuation,
                )
                for (
                    linked_account_id,
                    effective_snapshot_id,
                ), valuation in linked_accounts_valuation.items()
            ]
        )

    sub_accounts_valuation = get_sub_accounts_valuation(snapshot_data)
    logging.info("fetched sub accounts valuation")
    logging.debug(pretty_dump(sub_accounts_valuation))

    with db_session.persist(history_entry):
        history_entry.sub_accounts_valuation_history_entries.extend(
            [
                SubAccountValuationHistoryEntry(
                    linked_account_id=linked_account_id,
                    sub_account_id=sub_account_id,
                    sub_account_ccy=sub_account_ccy,
                    sub_account_description=sub_account_description,
                    sub_account_type=sub_account_type,
                    valuation=snapshot_valuation,
                    valuation_sub_account_ccy=account_valuation,
                )
                for (
                    linked_account_id,
                    sub_account_id,
                    sub_account_ccy,
                    sub_account_description,
                    sub_account_type,
                ), (
                    snapshot_valuation,
                    account_valuation,
                ) in sub_accounts_valuation.items()
            ]
        )

    with db_session.persist(history_entry):
        history_entry.sub_accounts_items_valuation_history_entries.extend(
            list(iter_sub_accounts_valuation_history_entries(snapshot_data))
        )

    logging.info("handling valuation change calculations")

    reference_history_entry_ids = repo.get_reference_history_entry_ids(
        baseline_id=history_entry.id,
        user_account_id=snapshot.user_account_id,
        valuation_date=valuation_date,
    )

    logging.info("reference history entry ids")
    logging.debug(pretty_dump(reference_history_entry_ids))

    user_account_valuation_change = repo.get_user_account_valuation_change(
        reference_history_entry_ids
    )

    logging.info("fetched user account valuation change")
    logging.debug(pretty_dump(user_account_valuation_change))

    with db_session.persist(history_entry):
        entry = history_entry.user_account_valuation_history_entry
        entry.valuation_change = user_account_valuation_change

    linked_accounts_valuation_change = repo.get_linked_accounts_valuation_change(
        reference_history_entry_ids
    )

    logging.info("fetched linked accounts valuation change")
    logging.debug(pretty_dump(linked_accounts_valuation_change))

    with db_session.persist(history_entry):
        for entry in history_entry.linked_accounts_valuation_history_entries:
            entry.valuation_change = linked_accounts_valuation_change[
                entry.linked_account_id
            ]

    sub_accounts_valuation_change = repo.get_sub_accounts_valuation_change(
        reference_history_entry_ids
    )

    logging.info("fetched sub accounts valuation change")
    logging.debug(pretty_dump(sub_accounts_valuation_change))

    with db_session.persist(history_entry):
        for entry in history_entry.sub_accounts_valuation_history_entries:
            path = (entry.linked_account_id, entry.sub_account_id)
            entry.valuation_change = sub_accounts_valuation_change[path]

    sub_accounts_items_valuation_change = repo.get_sub_accounts_items_valuation_change(
        reference_history_entry_ids
    )

    logging.info("fetched sub accounts items valuation change")
    logging.debug(pretty_dump(sub_accounts_items_valuation_change))

    with db_session.persist(history_entry):
        for entry in history_entry.sub_accounts_items_valuation_history_entries:
            path = (
                entry.linked_account_id,
                entry.sub_account_id,
                entry.item_type.name,
                entry.name,
            )
            entry.valuation_change = sub_accounts_items_valuation_change[path]

    with db_session.persist(history_entry):
        history_entry.available = True

    logging.info("new history entry added and enabled successfully")

    return jsonify(
        serialize(
            {
                "report": {
                    "history_entry_id": history_entry.id,
                    "valuation_date": valuation_date,
                    "user_account_valuation": user_account_valuation,
                    "valuation_change": user_account_valuation_change,
                }
            }
        )
    )
