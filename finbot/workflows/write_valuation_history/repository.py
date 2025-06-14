import dataclasses
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, TypeAlias, cast

from sqlalchemy.sql import text

from finbot import model
from finbot.core.db.utils import row_to_dict
from finbot.model import SessionType


@dataclasses.dataclass(frozen=True, eq=True)
class LinkedAccountKey:
    linked_account_id: int


@dataclasses.dataclass(frozen=True, eq=True)
class SubAccountKey:
    linked_account_id: int
    sub_account_id: str


@dataclasses.dataclass(frozen=True, eq=True)
class SubAccountItemKey:
    linked_account_id: int
    sub_account_id: str
    item_type: str
    name: str


@dataclasses.dataclass(frozen=True, eq=True)
class LinkedAccountValuationDescriptor:
    linked_account_id: int
    snapshot_id: int


@dataclasses.dataclass(frozen=True, eq=True)
class SubAccountValuationDescriptor:
    linked_account_id: int
    sub_account_id: str
    sub_account_ccy: str
    sub_account_description: str
    sub_account_type: str
    sub_account_sub_type: str | None


@dataclasses.dataclass
class SubAccountValuationAgg:
    value_sub_account_ccy: Decimal = dataclasses.field(default_factory=Decimal)
    value_snapshot_ccy: Decimal = dataclasses.field(default_factory=Decimal)

    def agg(self, value_sub_account_ccy: Decimal, value_snapshot_ccy: Decimal) -> None:
        self.value_sub_account_ccy += value_sub_account_ccy
        self.value_snapshot_ccy += value_snapshot_ccy


@dataclasses.dataclass(frozen=True)
class ConsistencySnapshotEntryHeader:
    snapshot_id: int
    linked_account_snapshot_entry_id: int
    linked_account_id: int
    sub_account_id: str
    sub_account_ccy: str
    sub_account_description: str
    sub_account_type: str
    sub_account_sub_type: str | None

    @property
    def linked_account_valuation_descriptor(self) -> LinkedAccountValuationDescriptor:
        return LinkedAccountValuationDescriptor(
            linked_account_id=self.linked_account_id,
            snapshot_id=self.snapshot_id,
        )

    @property
    def sub_account_valuation_descriptor(self) -> SubAccountValuationDescriptor:
        return SubAccountValuationDescriptor(
            linked_account_id=self.linked_account_id,
            sub_account_id=self.sub_account_id,
            sub_account_ccy=self.sub_account_ccy,
            sub_account_description=self.sub_account_description,
            sub_account_type=self.sub_account_type,
            sub_account_sub_type=self.sub_account_sub_type,
        )


@dataclasses.dataclass(frozen=True)
class ConsistencySnapshotItemEntry(ConsistencySnapshotEntryHeader):
    item_name: str
    item_type: model.SubAccountItemType
    item_subtype: str
    item_asset_class: str | None
    item_asset_type: str | None
    item_units: Decimal | None
    value_snapshot_ccy: Decimal
    value_sub_account_ccy: Decimal
    value_item_ccy: Decimal
    item_provider_specific_data: dict[str, Any] | None
    item_currency: str | None
    item_isin_code: str | None

    def get_value_snapshot_ccy(self) -> Decimal:
        return self.value_snapshot_ccy

    def get_value_sub_account_ccy(self) -> Decimal:
        return self.value_sub_account_ccy


@dataclasses.dataclass(frozen=True)
class ConsistencySnapshotEmptySubAccountEntry(ConsistencySnapshotEntryHeader):
    @staticmethod
    def get_value_snapshot_ccy() -> Decimal:
        return Decimal(0.0)

    @staticmethod
    def get_value_sub_account_ccy() -> Decimal:
        return Decimal(0.0)


ConsistencySnapshotEntry: TypeAlias = ConsistencySnapshotItemEntry | ConsistencySnapshotEmptySubAccountEntry


@dataclasses.dataclass(frozen=True)
class ConsistentSnapshot:
    snapshot_data: list[ConsistencySnapshotEntry]

    def __len__(self) -> int:
        return len(self.snapshot_data)

    def get_user_account_valuation(self) -> Decimal:
        return Decimal(sum(entry.get_value_snapshot_ccy() for entry in self.snapshot_data))

    def get_user_account_liabilities(self) -> Decimal:
        return Decimal(
            sum(entry.get_value_snapshot_ccy() for entry in self.snapshot_data if entry.get_value_snapshot_ccy() < 0)
        )

    def get_linked_accounts_valuation(
        self,
    ) -> dict[LinkedAccountValuationDescriptor, Decimal]:
        result: dict[LinkedAccountValuationDescriptor, Decimal] = defaultdict(Decimal)
        for entry in self.snapshot_data:
            result[entry.linked_account_valuation_descriptor] += entry.get_value_snapshot_ccy()
        return result

    def get_sub_accounts_valuation(
        self,
    ) -> dict[SubAccountValuationDescriptor, SubAccountValuationAgg]:
        result: dict[SubAccountValuationDescriptor, SubAccountValuationAgg] = defaultdict(SubAccountValuationAgg)
        for entry in self.snapshot_data:
            result[entry.sub_account_valuation_descriptor].agg(
                value_sub_account_ccy=entry.get_value_sub_account_ccy(),
                value_snapshot_ccy=entry.get_value_snapshot_ccy(),
            )
        return result


@dataclasses.dataclass(frozen=True)
class ReferenceHistoryEntryIds:
    baseline_id: int
    change_1h_id: int
    change_1d_id: int
    change_1w_id: int
    change_1m_id: int
    change_6m_id: int
    change_1y_id: int
    change_2y_id: int


class ReportRepository(object):
    def __init__(self, db_session: SessionType):
        self._db_session = db_session

    def get_consistent_snapshot_data(self, snapshot_id: int) -> ConsistentSnapshot:
        query = """
            SELECT slas.snapshot_id AS snapshot_id,
                   sase.linked_account_snapshot_entry_id AS linked_account_snapshot_entry_id,
                   slas.linked_account_id AS linked_account_id,
                   sase.sub_account_id AS sub_account_id,
                   sase.sub_account_ccy AS sub_account_ccy,
                   sase.sub_account_description AS sub_account_description,
                   sase.sub_account_type AS sub_account_type,
                   sase.sub_account_sub_type as sub_account_sub_type,
                   sais.name AS item_name,
                   sais.item_type AS item_type,
                   sais.item_subtype AS item_subtype,
                   sais.asset_class AS item_asset_class,
                   sais.asset_type AS item_asset_type,
                   sais.units AS item_units,
                   sais.value_snapshot_ccy AS value_snapshot_ccy,
                   sais.value_sub_account_ccy AS value_sub_account_ccy,
                   sais.value_item_ccy AS value_item_ccy,
                   sais.currency AS item_currency,
                   sais.isin_code AS item_isin_code,
                   sais.provider_specific_data AS item_provider_specific_data
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
                    AND NOT la.deleted
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
            LEFT JOIN finbot_sub_accounts_items_snapshot_entries sais
              ON sais.sub_account_snapshot_entry_id = sase.id
        """
        results = self._db_session.execute(text(query), {"snapshot_id": snapshot_id})
        return ConsistentSnapshot(
            snapshot_data=[_parse_consistent_snapshot_data_row(row_to_dict(row)) for row in results]
        )

    def get_reference_history_entry_ids(
        self, baseline_id: int, user_account_id: int, valuation_date: date
    ) -> ReferenceHistoryEntryIds:
        """Return user account history entry identifiers for different 'reference'
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
        results = self._db_session.execute(
            text(query),
            {"user_account_id": user_account_id, "valuation_date": valuation_date},
        )
        raw_reference_ids = row_to_dict(next(results))
        raw_reference_ids["baseline_id"] = baseline_id
        return ReferenceHistoryEntryIds(**raw_reference_ids)

    def get_user_account_valuation_change(
        self,
        reference_ids: ReferenceHistoryEntryIds,
    ) -> model.ValuationChangeEntry:
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
        row = next(self._db_session.execute(text(query), dataclasses.asdict(reference_ids)))
        return model.ValuationChangeEntry(**row_to_dict(row))

    def get_linked_accounts_valuation_change(
        self,
        reference_ids: ReferenceHistoryEntryIds,
    ) -> dict[LinkedAccountKey, model.ValuationChangeEntry]:
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
        rows = self._db_session.execute(text(query), dataclasses.asdict(reference_ids))
        results: dict[LinkedAccountKey, model.ValuationChangeEntry] = {}
        for row in rows:
            row = row_to_dict(row)
            descriptor = LinkedAccountKey(linked_account_id=row["linked_account_id"])
            results[descriptor] = model.ValuationChangeEntry(
                **({k: v for k, v in row.items() if k.startswith("change_")})
            )
        return results

    def get_sub_accounts_valuation_change(
        self,
        reference_ids: ReferenceHistoryEntryIds,
    ) -> dict[SubAccountKey, model.ValuationChangeEntry]:
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
        rows = self._db_session.execute(text(query), dataclasses.asdict(reference_ids))
        results: dict[SubAccountKey, model.ValuationChangeEntry] = {}
        for row in rows:
            row = row_to_dict(row)
            descriptor = SubAccountKey(
                linked_account_id=row["linked_account_id"],
                sub_account_id=row["sub_account_id"],
            )
            results[descriptor] = model.ValuationChangeEntry(
                **({k: v for k, v in row.items() if k.startswith("change_")})
            )
        return results

    def get_sub_accounts_items_valuation_change(
        self,
        reference_ids: ReferenceHistoryEntryIds,
    ) -> dict[SubAccountItemKey, model.ValuationChangeEntry]:
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
        rows = self._db_session.execute(text(query), dataclasses.asdict(reference_ids))
        results: dict[SubAccountItemKey, model.ValuationChangeEntry] = {}
        for row in rows:
            row = row_to_dict(row)
            descriptor = SubAccountItemKey(
                linked_account_id=row["linked_account_id"],
                sub_account_id=row["sub_account_id"],
                item_type=row["item_type"],
                name=row["item_name"],
            )
            results[descriptor] = model.ValuationChangeEntry(
                **({k: v for k, v in row.items() if k.startswith("change_")})
            )
        return results


def _parse_provider_specific_data(raw_data: str | None) -> dict[str, Any] | None:
    if raw_data is None:
        return None
    return cast(dict[str, Any], json.loads(raw_data))


def _parse_consistent_snapshot_data_row(
    row_data: dict[str, Any],
) -> ConsistencySnapshotEntry:
    row_data["item_provider_specific_data"] = _parse_provider_specific_data(row_data["item_provider_specific_data"])
    item_type = row_data["item_type"]
    if not item_type:
        keep_fields = {field.name for field in dataclasses.fields(ConsistencySnapshotEmptySubAccountEntry)}
        return ConsistencySnapshotEmptySubAccountEntry(
            **{field: value for (field, value) in row_data.items() if field in keep_fields}
        )
    row_data["item_type"] = model.SubAccountItemType[row_data["item_type"]]
    return ConsistencySnapshotItemEntry(**row_data)
