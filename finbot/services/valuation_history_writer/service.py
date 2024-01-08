import json
import logging
from typing import Any, Generator, cast

from finbot import model
from finbot.core import schema as core_schema
from finbot.core.db.session import Session
from finbot.core.serialization import pretty_dump, to_pydantic
from finbot.core.utils import some
from finbot.services.valuation_history_writer import repository, schema


def deserialize_provider_specific_data(raw_data: str | None) -> dict[str, Any] | None:
    if raw_data is None:
        return None
    return cast(dict[str, Any], json.loads(raw_data))


def iter_sub_account_item_valuation_history_entries(
    consistent_snapshot: repository.ConsistentSnapshot,
) -> Generator[model.SubAccountItemValuationHistoryEntry, None, None]:
    for entry in consistent_snapshot.snapshot_data:
        if isinstance(entry, repository.ConsistencySnapshotItemEntry):
            yield model.SubAccountItemValuationHistoryEntry(
                linked_account_id=entry.linked_account_id,
                sub_account_id=entry.sub_account_id,
                item_type=entry.item_type,
                name=entry.item_name,
                item_subtype=entry.item_subtype,
                asset_class=entry.item_asset_class,
                asset_type=entry.item_asset_type,
                units=entry.item_units,
                valuation=entry.value_snapshot_ccy,
                valuation_sub_account_ccy=entry.value_sub_account_ccy,
                valuation_item_ccy=entry.value_item_ccy,
                currency=entry.item_currency,
                provider_specific_data=entry.item_provider_specific_data,
            )


def write_history_impl(
    snapshot_id: int,
    db_session: Session,
) -> schema.WriteHistoryResponse:
    repo = repository.ReportRepository(db_session)

    logging.info("fetching snapshot_id={} metadata".format(snapshot_id))
    snapshot: model.UserAccountSnapshot = db_session.query(model.UserAccountSnapshot).filter_by(id=snapshot_id).one()

    valuation_date = some(snapshot.end_time)

    logging.info(f"snapshot is effective_at={valuation_date}")
    logging.info("fetching consistent snapshot")
    consistent_snapshot = repo.get_consistent_snapshot_data(snapshot_id)

    logging.info(f"consistent snapshot has entries={len(consistent_snapshot)}")
    logging.info("creating new history entry (marked not available)")

    with db_session.persist(model.UserAccountHistoryEntry()) as history_entry:
        history_entry.user_account_id = snapshot.user_account_id
        history_entry.source_snapshot_id = snapshot_id
        history_entry.effective_at = valuation_date
        history_entry.valuation_ccy = snapshot.requested_ccy
        history_entry.user_account_id = snapshot.user_account_id
        history_entry.available = False

    logging.info("handling basic valuation")

    user_account_valuation = consistent_snapshot.get_user_account_valuation()
    with db_session.persist(history_entry):
        history_entry.user_account_valuation_history_entry = model.UserAccountValuationHistoryEntry(
            valuation=consistent_snapshot.get_user_account_valuation(),
            total_liabilities=consistent_snapshot.get_user_account_liabilities(),
        )

    linked_accounts_valuation = consistent_snapshot.get_linked_accounts_valuation()
    logging.debug(pretty_dump(linked_accounts_valuation))

    with db_session.persist(history_entry):
        history_entry.linked_accounts_valuation_history_entries.extend(
            [
                model.LinkedAccountValuationHistoryEntry(
                    linked_account_id=descriptor.linked_account_id,
                    effective_snapshot_id=descriptor.snapshot_id,
                    valuation=valuation,
                )
                for (descriptor, valuation) in linked_accounts_valuation.items()
            ]
        )

    sub_accounts_valuation = consistent_snapshot.get_sub_accounts_valuation()
    logging.debug(pretty_dump(sub_accounts_valuation))

    with db_session.persist(history_entry):
        history_entry.sub_accounts_valuation_history_entries.extend(
            [
                model.SubAccountValuationHistoryEntry(
                    linked_account_id=descriptor.linked_account_id,
                    sub_account_id=descriptor.sub_account_id,
                    sub_account_ccy=descriptor.sub_account_ccy,
                    sub_account_description=descriptor.sub_account_description,
                    sub_account_type=descriptor.sub_account_type,
                    sub_account_sub_type=descriptor.sub_account_sub_type,
                    valuation=valuation.value_snapshot_ccy,
                    valuation_sub_account_ccy=valuation.value_sub_account_ccy,
                )
                for (descriptor, valuation) in sub_accounts_valuation.items()
            ]
        )

    with db_session.persist(history_entry):
        history_entry.sub_accounts_items_valuation_history_entries.extend(
            list(iter_sub_account_item_valuation_history_entries(consistent_snapshot))
        )

    logging.info("handling valuation change calculations")

    reference_history_entry_ids = repo.get_reference_history_entry_ids(
        baseline_id=history_entry.id,
        user_account_id=snapshot.user_account_id,
        valuation_date=valuation_date,
    )

    logging.info("reference history entry ids")
    logging.debug(pretty_dump(reference_history_entry_ids))

    user_account_valuation_change = repo.get_user_account_valuation_change(reference_history_entry_ids)

    logging.info("fetched user account valuation change")
    logging.debug(pretty_dump(user_account_valuation_change))

    with db_session.persist(history_entry):
        history_entry.user_account_valuation_history_entry.valuation_change = user_account_valuation_change

    linked_accounts_valuation_change = repo.get_linked_accounts_valuation_change(reference_history_entry_ids)

    logging.info("fetched linked accounts valuation change")
    logging.debug(pretty_dump(linked_accounts_valuation_change))

    with db_session.persist(history_entry):
        for linked_accounts_valuation_history_entry in history_entry.linked_accounts_valuation_history_entries:
            linked_accounts_valuation_history_entry.valuation_change = linked_accounts_valuation_change[
                repository.LinkedAccountKey(linked_account_id=linked_accounts_valuation_history_entry.linked_account_id)
            ]

    sub_accounts_valuation_change = repo.get_sub_accounts_valuation_change(reference_history_entry_ids)

    logging.info("fetched sub accounts valuation change")
    logging.debug(pretty_dump(sub_accounts_valuation_change))

    with db_session.persist(history_entry):
        for entry in history_entry.sub_accounts_valuation_history_entries:
            entry.valuation_change = sub_accounts_valuation_change[
                repository.SubAccountKey(
                    linked_account_id=entry.linked_account_id,
                    sub_account_id=entry.sub_account_id,
                )
            ]

    sub_accounts_items_valuation_change = repo.get_sub_accounts_items_valuation_change(reference_history_entry_ids)

    logging.info("fetched sub accounts items valuation change")
    logging.debug(pretty_dump(sub_accounts_items_valuation_change))

    with db_session.persist(history_entry):
        for sub_accounts_items_valuation_history_entry in history_entry.sub_accounts_items_valuation_history_entries:
            sub_accounts_items_valuation_history_entry.valuation_change = sub_accounts_items_valuation_change[
                repository.SubAccountItemKey(
                    linked_account_id=sub_accounts_items_valuation_history_entry.linked_account_id,
                    sub_account_id=sub_accounts_items_valuation_history_entry.sub_account_id,
                    item_type=sub_accounts_items_valuation_history_entry.item_type.name,
                    name=sub_accounts_items_valuation_history_entry.name,
                )
            ]

    with db_session.persist(history_entry):
        history_entry.available = True

    logging.info("new history entry added and enabled successfully")

    return schema.WriteHistoryResponse(
        report=schema.NewHistoryEntryReport(
            history_entry_id=history_entry.id,
            valuation_date=valuation_date,
            valuation_currency=history_entry.valuation_ccy,
            user_account_valuation=float(user_account_valuation),
            valuation_change=to_pydantic(core_schema.ValuationChange, user_account_valuation_change),
        )
    )


class ValuationHistoryWriterService(object):
    def __init__(self, db_session: Session):
        self._db_session = db_session

    def write_history(self, snapshot_id: int) -> schema.WriteHistoryResponse:
        return write_history_impl(snapshot_id=snapshot_id, db_session=self._db_session)
