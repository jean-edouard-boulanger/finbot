from finbot.model import (
    ValuationChangeEntry
)
import logging
import pandas as pd


def get_consistent_snapshot_data(db_session, snapshot_id):
    query = """
        SELECT uas.id AS snapshot_id,
            uas.end_time AS snapshot_effective_time,
            sase.linked_account_snapshot_entry_id AS linked_account_snapshot_entry_id,
            sase.sub_account_id AS sub_account_id,
            sais.sub_account_snapshot_entry_id AS sub_account_snapshot_entry_id,
            sais.id AS sub_account_item_snapshot_entry_id,
            sais.name AS item_name,
            sais.item_type AS item_type,
            sais.item_subtype AS item_subtype,
            sais.units AS item_units,
            sais.value_snapshot_ccy
        FROM (
            SELECT las.snapshot_id AS snapshot_id,
                las.linked_account_id, MAX(las.id) AS linked_account_snapshot_entry_id
            FROM finbot_linked_accounts_snapshots las
            JOIN (
                SELECT la.id FROM finbot_linked_accounts la
                JOIN finbot_user_accounts_snapshots uas 
                ON uas.user_account_id = la.user_account_id 
                WHERE uas.id = :snapshot_id
                AND NOT deleted
            ) AS la ON la.id = las.linked_account_id
            WHERE success
            AND las.snapshot_id <= :snapshot_id
            GROUP BY las.snapshot_id, las.linked_account_id
        ) slas
        JOIN finbot_user_accounts_snapshots uas ON slas.snapshot_id = uas.id
        JOIN finbot_sub_accounts_snapshot_entries sase ON sase.linked_account_snapshot_entry_id = slas.linked_account_snapshot_entry_id
        JOIN finbot_sub_accounts_items_snapshot_entries sais ON sais.sub_account_snapshot_entry_id = sase.id
    """
    results = db_session.execute(query, {"snapshot_id": snapshot_id})
    return pd.DataFrame([dict(row) for row in results])


def get_linked_accounts_valuation_change(db_session, valuation_date, 
                                         linked_accounts_amounts):
    pass


def get_user_account_valuation_change(db_session, user_account_id, 
                                      valuation_date, current_amount):
    query = """
        SELECT uavh.amount AS amount
          FROM finbot_user_accounts_valuation_history_entries uavh
          JOIN finbot_user_accounts_history_entries uahe
            ON uavh.history_entry_id = uahe.id
         WHERE uahe.user_account_id = :user_account_id
           AND uahe.effective_at <= (:valuation_date - INTERVAL :interval)
      ORDER BY uahe.effective_at DESC
         LIMIT 1
    """

    handlers = {
        "change_1day": "1 day",
        "change_1week": "1 week",
        "change_1month": "1 month",
        "change_6months": "6 months",
        "change_1year": "1 year",
        "change_2years": "2 years"
    }

    change_entry = ValuationChangeEntry()
    for field, interval in handlers.items():
        results = db_session.execute(query, {
            "user_account_id": user_account_id,
            "valuation_date": valuation_date,
            "interval": interval
        })
        results = [row for row in results]
        if results:
            delta = float(current_amount - results[0]["amount"])
            logging.info((interval, delta))
            setattr(change_entry, field, delta)
    return change_entry