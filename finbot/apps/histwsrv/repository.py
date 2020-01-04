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
