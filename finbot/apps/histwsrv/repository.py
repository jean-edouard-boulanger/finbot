from finbot.model import ValuationChangeEntry
import pandas as pd


class ReportRepository(object):
    def __init__(self, db_session):
        self.db_session = db_session

    def get_consistent_snapshot_data(self, snapshot_id):
        query = """
            SELECT slas.snapshot_id AS snapshot_id,
                   sase.linked_account_snapshot_entry_id AS linked_account_snapshot_entry_id,
                   slas.linked_account_id AS linked_account_id,
                   sase.sub_account_id AS sub_account_id,
                   sase.sub_account_ccy AS sub_account_ccy,
                   sase.sub_account_description AS sub_account_description,
                   sais.sub_account_snapshot_entry_id AS sub_account_snapshot_entry_id,
                   sais.id AS sub_account_item_snapshot_entry_id,
                   sais.name AS item_name,
                   sais.item_type AS item_type,
                   sais.item_subtype AS item_subtype,
                   sais.units AS item_units,
                   sais.value_snapshot_ccy AS value_snapshot_ccy,
                   sais.value_sub_account_ccy AS value_sub_account_ccy
            FROM (
                -- Find the latest linked account snapshot entry in a
                -- successful snapshot (can be the requested raw snapshot or any
                -- that was taken before) for each linked account belonging
                -- to the user.

                SELECT las.linked_account_id AS linked_account_id,
                       MAX(las.snapshot_id) AS snapshot_id
                FROM finbot_linked_accounts_snapshots las
                JOIN (
                    -- Find all active linked accounts owned by the user 
                    -- the requested raw snapshot was created for.

                    SELECT la.id FROM finbot_linked_accounts la
                    JOIN finbot_user_accounts_snapshots uas 
                    ON uas.user_account_id = la.user_account_id 
                    WHERE uas.id = :snapshot_id
                    AND NOT deleted
                ) AS la ON la.id = las.linked_account_id
                WHERE success
                AND las.snapshot_id <= :snapshot_id
                GROUP BY las.linked_account_id
            ) AS slas
            JOIN finbot_linked_accounts_snapshots las
              ON las.snapshot_id = slas.snapshot_id
             AND las.linked_account_id = slas.linked_account_id
            JOIN finbot_sub_accounts_snapshot_entries sase 
              ON sase.linked_account_snapshot_entry_id = las.id
            JOIN finbot_sub_accounts_items_snapshot_entries sais 
              ON sais.sub_account_snapshot_entry_id = sase.id
        """
        results = self.db_session.execute(query, {"snapshot_id": snapshot_id})
        return pd.DataFrame([dict(row) for row in results])

    def get_reference_history_entry_ids(self, baseline_id, user_account_id, 
                                        valuation_date):
        """ Return user account history entry identifiers for different 'reference'
        dates in the past (1 day, 1 month, 6 months, 1 year, 2 years)
        """
        query = """
            SELECT c1h.id AS change_1h_id,
                   c1d.id AS change_1d_id,
                   c1w.id AS change_1w_id,
                   c1m.id AS change_1m_id,
                   c6m.id AS change_6m_id,
                   c1y.id AS change_1y_id,
                   c2y.id AS change_2y_id
            FROM (VALUES (1)) AS dummy (pk)
            LEFT JOIN (
                SELECT 1 AS pk, id
                FROM finbot_user_accounts_history_entries
                WHERE effective_at <= (:valuation_date - INTERVAL '1 hour')
                AND user_account_id = :user_account_id
                AND available
                ORDER BY effective_at DESC
                LIMIT 1
            ) AS c1h ON dummy.pk = c1h.pk
            LEFT JOIN (
                SELECT 1 AS pk, id
                FROM finbot_user_accounts_history_entries
                WHERE effective_at <= (:valuation_date - INTERVAL '1 day')
                AND user_account_id = :user_account_id
                AND available
                ORDER BY effective_at DESC
                LIMIT 1
            ) AS c1d ON dummy.pk = c1d.pk
            LEFT JOIN (
                SELECT 1 AS pk, id
                FROM finbot_user_accounts_history_entries
                WHERE effective_at <= (:valuation_date - INTERVAL '1 week')
                AND user_account_id = :user_account_id
                AND available
                ORDER BY effective_at DESC
                LIMIT 1
            ) AS c1w ON dummy.pk = c1w.pk
            LEFT JOIN (
                SELECT 1 AS pk, id
                FROM finbot_user_accounts_history_entries
                WHERE effective_at <= (:valuation_date - INTERVAL '1 month')
                AND user_account_id = :user_account_id
                AND available
                ORDER BY effective_at DESC
                LIMIT 1
            ) AS c1m ON dummy.pk = c1m.pk
            LEFT JOIN (
                SELECT 1 AS pk, id
                FROM finbot_user_accounts_history_entries
                WHERE effective_at <= (:valuation_date - INTERVAL '6 months')
                AND user_account_id = :user_account_id
                AND available
                ORDER BY effective_at DESC
                LIMIT 1
            ) AS c6m ON dummy.pk = c6m.pk
            LEFT JOIN (
                SELECT 1 AS pk, id
                FROM finbot_user_accounts_history_entries
                WHERE effective_at <= (:valuation_date - INTERVAL '1 year')
                AND user_account_id = :user_account_id
                AND available
                ORDER BY effective_at DESC
                LIMIT 1
            ) AS c1y ON dummy.pk = c1y.pk
            LEFT JOIN (
                SELECT 1 AS pk, id
                FROM finbot_user_accounts_history_entries
                WHERE effective_at <= (:valuation_date - INTERVAL '2 years')
                AND user_account_id = :user_account_id
                AND available
                ORDER BY effective_at DESC
                LIMIT 1
            ) AS c2y ON dummy.pk = c2y.pk
        """
        results = self.db_session.execute(query, {
            "user_account_id": user_account_id,
            "valuation_date": valuation_date
        })
        past_results = dict(next(results))
        past_results["baseline_id"] = baseline_id
        return past_results

    def get_user_account_valuation_change(self, reference_ids):
        query = """
            SELECT val.valuation - val_c1h.valuation AS change_1hour,
                   val.valuation - val_c1d.valuation AS change_1day,
                   val.valuation - val_c1w.valuation AS change_1week,
                   val.valuation - val_c1m.valuation AS change_1month,
                   val.valuation - val_c6m.valuation AS change_6months,
                   val.valuation - val_c1y.valuation AS change_1year,
                   val.valuation - val_c2y.valuation AS change_2years
              FROM finbot_user_accounts_valuation_history_entries val
         LEFT JOIN finbot_user_accounts_valuation_history_entries val_c1h
                ON val_c1h.history_entry_id = :change_1h_id
         LEFT JOIN finbot_user_accounts_valuation_history_entries val_c1d
                ON val_c1d.history_entry_id = :change_1d_id
         LEFT JOIN finbot_user_accounts_valuation_history_entries val_c1w
                ON val_c1w.history_entry_id = :change_1w_id
         LEFT JOIN finbot_user_accounts_valuation_history_entries val_c1m
                ON val_c1m.history_entry_id = :change_1m_id
         LEFT JOIN finbot_user_accounts_valuation_history_entries val_c6m
                ON val_c6m.history_entry_id = :change_6m_id
         LEFT JOIN finbot_user_accounts_valuation_history_entries val_c1y
                ON val_c1y.history_entry_id = :change_1y_id
         LEFT JOIN finbot_user_accounts_valuation_history_entries val_c2y
                ON val_c2y.history_entry_id = :change_2y_id
             WHERE val.history_entry_id = :baseline_id
        """
        row = next(self.db_session.execute(query, reference_ids))
        return ValuationChangeEntry(**dict(row))

    def get_linked_accounts_valuation_change(self, reference_ids):
        query = """
            SELECT val.linked_account_id AS linked_account_id,
                   val.valuation - val_c1h.valuation AS change_1hour,
                   val.valuation - val_c1d.valuation AS change_1day,
                   val.valuation - val_c1w.valuation AS change_1week,
                   val.valuation - val_c1m.valuation AS change_1month,
                   val.valuation - val_c6m.valuation AS change_6months,
                   val.valuation - val_c1y.valuation AS change_1year,
                   val.valuation - val_c2y.valuation AS change_2years
              FROM finbot_linked_accounts_valuation_history_entries val
         LEFT JOIN finbot_linked_accounts_valuation_history_entries val_c1h
                ON val_c1h.linked_account_id = val.linked_account_id
               AND val_c1h.history_entry_id = :change_1h_id
         LEFT JOIN finbot_linked_accounts_valuation_history_entries val_c1d
                ON val_c1d.linked_account_id = val.linked_account_id
               AND val_c1d.history_entry_id = :change_1d_id
         LEFT JOIN finbot_linked_accounts_valuation_history_entries val_c1w
                ON val_c1w.linked_account_id = val.linked_account_id
               AND val_c1w.history_entry_id = :change_1w_id
         LEFT JOIN finbot_linked_accounts_valuation_history_entries val_c1m
                ON val_c1m.linked_account_id = val.linked_account_id
               AND val_c1m.history_entry_id = :change_1m_id
         LEFT JOIN finbot_linked_accounts_valuation_history_entries val_c6m
                ON val_c6m.linked_account_id = val.linked_account_id
               AND val_c6m.history_entry_id = :change_6m_id
         LEFT JOIN finbot_linked_accounts_valuation_history_entries val_c1y
                ON val_c1y.linked_account_id = val.linked_account_id
               AND val_c1y.history_entry_id = :change_1y_id
         LEFT JOIN finbot_linked_accounts_valuation_history_entries val_c2y
                ON val_c2y.linked_account_id = val.linked_account_id
               AND val_c2y.history_entry_id = :change_2y_id
             WHERE val.history_entry_id = :baseline_id
        """
        rows = self.db_session.execute(query, reference_ids)
        results = {}
        for row in rows:
            row = dict(row)
            results[row["linked_account_id"]] = ValuationChangeEntry(
                **({k: v for k, v in row.items() if k.startswith("change_")}))
        return results

    def get_sub_accounts_valuation_change(self, reference_ids):
        query = """
            SELECT val.linked_account_id AS linked_account_id,
                   val.sub_account_id AS sub_account_id,
                   val.valuation - val_c1h.valuation AS change_1hour,
                   val.valuation - val_c1d.valuation AS change_1day,
                   val.valuation - val_c1w.valuation AS change_1week,
                   val.valuation - val_c1m.valuation AS change_1month,
                   val.valuation - val_c6m.valuation AS change_6months,
                   val.valuation - val_c1y.valuation AS change_1year,
                   val.valuation - val_c2y.valuation AS change_2years
              FROM finbot_sub_accounts_valuation_history_entries val
         LEFT JOIN finbot_sub_accounts_valuation_history_entries val_c1h
                ON val_c1h.linked_account_id = val.linked_account_id
               AND val_c1h.sub_account_id = val.sub_account_id
               AND val_c1h.history_entry_id = :change_1h_id
         LEFT JOIN finbot_sub_accounts_valuation_history_entries val_c1d
                ON val_c1d.linked_account_id = val.linked_account_id
               AND val_c1d.sub_account_id = val.sub_account_id
               AND val_c1d.history_entry_id = :change_1d_id
         LEFT JOIN finbot_sub_accounts_valuation_history_entries val_c1w
                ON val_c1w.linked_account_id = val.linked_account_id
               AND val_c1w.sub_account_id = val.sub_account_id
               AND val_c1w.history_entry_id = :change_1w_id
         LEFT JOIN finbot_sub_accounts_valuation_history_entries val_c1m
                ON val_c1m.linked_account_id = val.linked_account_id
               AND val_c1m.sub_account_id = val.sub_account_id
               AND val_c1m.history_entry_id = :change_1m_id
         LEFT JOIN finbot_sub_accounts_valuation_history_entries val_c6m
                ON val_c6m.linked_account_id = val.linked_account_id
               AND val_c6m.sub_account_id = val.sub_account_id
               AND val_c6m.history_entry_id = :change_6m_id
         LEFT JOIN finbot_sub_accounts_valuation_history_entries val_c1y
                ON val_c1y.linked_account_id = val.linked_account_id
               AND val_c1y.sub_account_id = val.sub_account_id
               AND val_c1y.history_entry_id = :change_1y_id
         LEFT JOIN finbot_sub_accounts_valuation_history_entries val_c2y
                ON val_c2y.linked_account_id = val.linked_account_id
               AND val_c2y.sub_account_id = val.sub_account_id
               AND val_c2y.history_entry_id = :change_2y_id
             WHERE val.history_entry_id = :baseline_id
        """
        rows = self.db_session.execute(query, reference_ids)
        results = {}
        for row in rows:
            row = dict(row)
            path = (row["linked_account_id"], row["sub_account_id"])
            results[path] = ValuationChangeEntry(
                **({k: v for k, v in row.items() if k.startswith("change_")}))
        return results

    def get_sub_accounts_items_valuation_change(self, reference_ids):
        query = """
            SELECT val.linked_account_id AS linked_account_id,
                   val.sub_account_id AS sub_account_id,
                   val.item_type AS item_type,
                   val.name AS item_name,
                   val.valuation - val_c1h.valuation AS change_1hour,
                   val.valuation - val_c1d.valuation AS change_1day,
                   val.valuation - val_c1w.valuation AS change_1week,
                   val.valuation - val_c1m.valuation AS change_1month,
                   val.valuation - val_c6m.valuation AS change_6months,
                   val.valuation - val_c1y.valuation AS change_1year,
                   val.valuation - val_c2y.valuation AS change_2years
              FROM finbot_sub_accounts_items_valuation_history_entries val
         LEFT JOIN finbot_sub_accounts_items_valuation_history_entries val_c1h
                ON val_c1h.linked_account_id = val.linked_account_id
               AND val_c1h.sub_account_id = val.sub_account_id
               AND val_c1h.item_type = val.item_type
               AND val_c1h.name = val.name
               AND val_c1h.history_entry_id = :change_1h_id
         LEFT JOIN finbot_sub_accounts_items_valuation_history_entries val_c1d
                ON val_c1d.linked_account_id = val.linked_account_id
               AND val_c1d.sub_account_id = val.sub_account_id
               AND val_c1d.item_type = val.item_type
               AND val_c1d.name = val.name
               AND val_c1d.history_entry_id = :change_1d_id
         LEFT JOIN finbot_sub_accounts_items_valuation_history_entries val_c1w
                ON val_c1w.linked_account_id = val.linked_account_id
               AND val_c1w.sub_account_id = val.sub_account_id
               AND val_c1w.item_type = val.item_type
               AND val_c1w.name = val.name
               AND val_c1w.history_entry_id = :change_1w_id
         LEFT JOIN finbot_sub_accounts_items_valuation_history_entries val_c1m
                ON val_c1m.linked_account_id = val.linked_account_id
               AND val_c1m.sub_account_id = val.sub_account_id
               AND val_c1m.item_type = val.item_type
               AND val_c1m.name = val.name
               AND val_c1m.history_entry_id = :change_1m_id
         LEFT JOIN finbot_sub_accounts_items_valuation_history_entries val_c6m
                ON val_c6m.linked_account_id = val.linked_account_id
               AND val_c6m.sub_account_id = val.sub_account_id
               AND val_c6m.item_type = val.item_type
               AND val_c6m.name = val.name
               AND val_c6m.history_entry_id = :change_6m_id
         LEFT JOIN finbot_sub_accounts_items_valuation_history_entries val_c1y
                ON val_c1y.linked_account_id = val.linked_account_id
               AND val_c1y.sub_account_id = val.sub_account_id
               AND val_c1y.item_type = val.item_type
               AND val_c1y.name = val.name
               AND val_c1y.history_entry_id = :change_1y_id
         LEFT JOIN finbot_sub_accounts_items_valuation_history_entries val_c2y
                ON val_c2y.linked_account_id = val.linked_account_id
               AND val_c2y.sub_account_id = val.sub_account_id
               AND val_c2y.item_type = val.item_type
               AND val_c2y.name = val.name
               AND val_c2y.history_entry_id = :change_1y_id
             WHERE val.history_entry_id = :baseline_id
        """
        rows = self.db_session.execute(query, reference_ids)
        results = {}
        for row in rows:
            row = dict(row)
            path = (
                row["linked_account_id"], row["sub_account_id"], 
                row["item_type"], row["item_name"]
            )
            results[path] = ValuationChangeEntry(
                **({k: v for k, v in row.items() if k.startswith("change_")}))
        return results
