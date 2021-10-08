from finbot.apps.histwsrv import repository
from finbot.core.web_service import service_endpoint
from finbot.core.serialization import pretty_dump
from finbot.core.logging import configure_logging
from finbot.core.db.session import Session
from finbot.core.utils import unwrap_optional
from finbot.core import tracer, environment
from finbot.model import (
    UserAccountSnapshot,
    UserAccountHistoryEntry,
    UserAccountValuationHistoryEntry,
    LinkedAccountValuationHistoryEntry,
    SubAccountValuationHistoryEntry,
    SubAccountItemValuationHistoryEntry,
)

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import pandas as pd

from typing import Any
from decimal import Decimal
import logging


FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)

db_engine = create_engine(FINBOT_ENV.database_url)
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))
tracer.configure(
    identity="hitwsrv", persistence_layer=tracer.DBPersistenceLayer(db_session)
)

app = Flask(__name__)


def get_user_account_valuation(data: pd.DataFrame) -> Decimal:
    return Decimal(data["value_snapshot_ccy"].sum())


def get_user_account_liabilities(data: pd.DataFrame) -> Decimal:
    return Decimal(data.loc[data["value_snapshot_ccy"] < 0, "value_snapshot_ccy"].sum())


def get_linked_accounts_valuation(data: pd.DataFrame) -> dict[Any, Any]:
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
@service_endpoint()
def healthy():
    return {"healthy": True}


@app.route("/history/<snapshot_id>/write", methods=["POST"])
@service_endpoint()
def write_history(snapshot_id: int):
    tracer.current().set_input({"snapshot_id": snapshot_id})
    repo = repository.ReportRepository(db_session)

    logging.info("fetching snapshot_id={} metadata".format(snapshot_id))
    snapshot: UserAccountSnapshot = (
        db_session.query(UserAccountSnapshot).filter_by(id=snapshot_id).one()
    )

    valuation_date = unwrap_optional(snapshot.end_time)

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
        history_entry.trace_guid = tracer.context_identifier()

    tracer.milestone("blank history entry created", output={"id": history_entry.id})

    logging.info("handling basic valuation")

    user_account_valuation = get_user_account_valuation(snapshot_data)
    tracer.milestone(
        "user account valuation", output={"valuation": user_account_valuation}
    )

    user_account_total_liabilities = get_user_account_liabilities(snapshot_data)
    tracer.milestone(
        "user account liabilities",
        output={"liabilities": user_account_total_liabilities},
    )

    with db_session.persist(history_entry):
        history_entry.user_account_valuation_history_entry = (
            UserAccountValuationHistoryEntry(
                valuation=user_account_valuation,
                total_liabilities=user_account_total_liabilities,
            )
        )

    linked_accounts_valuation = get_linked_accounts_valuation(snapshot_data)
    tracer.milestone(
        "linked accounts valuation", output={"valuation": linked_accounts_valuation}
    )
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
    tracer.milestone(
        "sub accounts valuation", output={"valuation": sub_accounts_valuation}
    )
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
        history_entry.user_account_valuation_history_entry.valuation_change = (
            user_account_valuation_change
        )

    linked_accounts_valuation_change = repo.get_linked_accounts_valuation_change(
        reference_history_entry_ids
    )

    logging.info("fetched linked accounts valuation change")
    logging.debug(pretty_dump(linked_accounts_valuation_change))

    with db_session.persist(history_entry):
        for (
            linked_accounts_valuation_history_entry
        ) in history_entry.linked_accounts_valuation_history_entries:
            linked_accounts_valuation_history_entry.valuation_change = (
                linked_accounts_valuation_change[
                    linked_accounts_valuation_history_entry.linked_account_id
                ]
            )

    sub_accounts_valuation_change = repo.get_sub_accounts_valuation_change(
        reference_history_entry_ids
    )

    logging.info("fetched sub accounts valuation change")
    logging.debug(pretty_dump(sub_accounts_valuation_change))

    with db_session.persist(history_entry):
        for entry in history_entry.sub_accounts_valuation_history_entries:
            entry.valuation_change = sub_accounts_valuation_change[
                (entry.linked_account_id, entry.sub_account_id)
            ]

    sub_accounts_items_valuation_change = repo.get_sub_accounts_items_valuation_change(
        reference_history_entry_ids
    )

    logging.info("fetched sub accounts items valuation change")
    logging.debug(pretty_dump(sub_accounts_items_valuation_change))

    with db_session.persist(history_entry):
        for (
            sub_accounts_items_valuation_history_entry
        ) in history_entry.sub_accounts_items_valuation_history_entries:
            sub_accounts_items_valuation_history_entry.valuation_change = (
                sub_accounts_items_valuation_change[
                    (
                        sub_accounts_items_valuation_history_entry.linked_account_id,
                        sub_accounts_items_valuation_history_entry.sub_account_id,
                        sub_accounts_items_valuation_history_entry.item_type.name,
                        sub_accounts_items_valuation_history_entry.name,
                    )
                ]
            )

    with db_session.persist(history_entry):
        history_entry.available = True

    logging.info("new history entry added and enabled successfully")

    return {
        "report": {
            "history_entry_id": history_entry.id,
            "valuation_date": valuation_date,
            "valuation_currency": history_entry.valuation_ccy,
            "user_account_valuation": user_account_valuation,
            "valuation_change": user_account_valuation_change,
        }
    }
