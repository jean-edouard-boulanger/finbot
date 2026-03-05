import logging
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql import text

from finbot import model
from finbot.model import SessionType
from finbot.providers.schema import TransactionType, category_for_type

logger = logging.getLogger(__name__)


def consolidate_transactions(
    snapshot_id: int,
    db_session: SessionType,
) -> list[int]:
    """Consolidate raw transaction snapshot entries into the permanent history table.

    Returns the IDs of newly inserted (not updated) TransactionHistoryEntry rows.
    """
    # 1. Read raw transaction snapshot entries for this snapshot
    raw_entries: list[model.TransactionsSnapshotEntry] = (
        db_session.query(model.TransactionsSnapshotEntry)
        .join(  # type: ignore[no-untyped-call]
            model.LinkedAccountSnapshotEntry,
            model.TransactionsSnapshotEntry.linked_account_snapshot_entry_id == model.LinkedAccountSnapshotEntry.id,
        )
        .filter(model.LinkedAccountSnapshotEntry.snapshot_id == snapshot_id)
        .all()
    )

    if not raw_entries:
        logger.info("no transaction snapshot entries found for snapshot_id=%d", snapshot_id)
        return []

    # 2. Read FX rates from snapshot
    xccy_rates: dict[str, Decimal] = {}
    for rate_entry in db_session.query(model.XccyRateSnapshotEntry).filter_by(snapshot_id=snapshot_id).all():
        xccy_rates[rate_entry.xccy_pair] = rate_entry.rate

    # 3. Get the snapshot's requested currency
    snapshot: model.UserAccountSnapshot = db_session.query(model.UserAccountSnapshot).filter_by(id=snapshot_id).one()
    target_ccy = snapshot.requested_ccy

    # 4. Process each raw entry
    new_ids: list[int] = []
    for raw_entry in raw_entries:
        linked_account_id = raw_entry.linked_account_snapshot_entry.linked_account_id
        transactions = raw_entry.transactions

        for txn_data in transactions:
            txn_type = TransactionType(txn_data["transaction_type"])
            txn_category = category_for_type(txn_type)
            amount = Decimal(str(txn_data["amount"]))
            currency = txn_data["currency"]

            # FX conversion
            amount_snapshot_ccy = _convert_amount(amount, currency, target_ccy, xccy_rates)

            # Determine spending category source
            spending_source = None
            if txn_data.get("spending_category_primary"):
                spending_source = "provider"

            # Upsert using INSERT ... ON CONFLICT DO UPDATE
            stmt = pg_insert(model.TransactionHistoryEntry).values(
                linked_account_id=linked_account_id,
                sub_account_id=txn_data["account_id"],
                provider_transaction_id=txn_data["transaction_id"],
                transaction_date=txn_data["transaction_date"],
                transaction_type=txn_type.value,
                transaction_category=txn_category.value,
                amount=amount,
                amount_snapshot_ccy=amount_snapshot_ccy,
                currency=currency,
                description=txn_data.get("description", "")[:512],
                symbol=txn_data.get("symbol"),
                units=Decimal(str(txn_data["units"])) if txn_data.get("units") is not None else None,
                unit_price=Decimal(str(txn_data["unit_price"])) if txn_data.get("unit_price") is not None else None,
                fee=Decimal(str(txn_data["fee"])) if txn_data.get("fee") is not None else None,
                counterparty=txn_data.get("counterparty"),
                spending_category_primary=txn_data.get("spending_category_primary"),
                spending_category_detailed=txn_data.get("spending_category_detailed"),
                spending_category_source=spending_source,
                provider_specific_data=txn_data.get("provider_specific"),
                source_snapshot_id=snapshot_id,
            )

            # ON CONFLICT: update most fields but preserve spending categories if already set
            stmt = stmt.on_conflict_do_update(
                constraint="uidx_transactions_history_dedup",
                set_={
                    "transaction_date": stmt.excluded.transaction_date,
                    "transaction_type": stmt.excluded.transaction_type,
                    "transaction_category": stmt.excluded.transaction_category,
                    "amount": stmt.excluded.amount,
                    "amount_snapshot_ccy": stmt.excluded.amount_snapshot_ccy,
                    "currency": stmt.excluded.currency,
                    "description": stmt.excluded.description,
                    "symbol": stmt.excluded.symbol,
                    "units": stmt.excluded.units,
                    "unit_price": stmt.excluded.unit_price,
                    "fee": stmt.excluded.fee,
                    "counterparty": stmt.excluded.counterparty,
                    "provider_specific_data": stmt.excluded.provider_specific_data,
                    "source_snapshot_id": stmt.excluded.source_snapshot_id,
                },
            )

            result = db_session.execute(stmt)
            db_session.flush()

            # Check if this was an insert (not an update) — collect for LLM categorization
            if result.rowcount == 1:
                # Retrieve the inserted/updated row's ID
                row = db_session.execute(
                    text(
                        "SELECT id, spending_category_source FROM finbot_transactions_history"
                        " WHERE linked_account_id = :la_id"
                        " AND sub_account_id = :sa_id"
                        " AND provider_transaction_id = :ptid"
                    ),
                    {
                        "la_id": linked_account_id,
                        "sa_id": txn_data["account_id"],
                        "ptid": txn_data["transaction_id"],
                    },
                ).fetchone()
                if row and row[1] is None:
                    new_ids.append(row[0])

    db_session.commit()

    logger.info(
        "consolidated transactions for snapshot_id=%d: %d new uncategorized entries",
        snapshot_id,
        len(new_ids),
    )
    return new_ids


def _convert_amount(
    amount: Decimal,
    currency: str,
    target_ccy: str,
    xccy_rates: dict[str, Decimal],
) -> Decimal | None:
    if currency == target_ccy:
        return amount
    xccy_pair = f"{currency}{target_ccy}"
    rate = xccy_rates.get(xccy_pair)
    if rate is not None:
        return amount * rate
    return None
