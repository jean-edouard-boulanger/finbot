# mypy: allow-untyped-calls
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import (
    Any,
    Literal,
    Optional,
    Protocol,
    Type,
    TypedDict,
    Union,
    cast,
    overload,
)

from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import text

from finbot.core.db.session import Session
from finbot.core.db.utils import row_to_dict
from finbot.core.errors import MissingUserData, ResourceNotFoundError
from finbot.core.schema import ValuationFrequency
from finbot.model import (
    LinkedAccount,
    LinkedAccountSnapshotEntry,
    LinkedAccountValuationHistoryEntry,
    Provider,
    SubAccountItemValuationHistoryEntry,
    SubAccountValuationHistoryEntry,
    UserAccount,
    UserAccountHistoryEntry,
    UserAccountSettings,
    UserAccountValuationHistoryEntry,
)
from finbot.providers.schema import AssetClass, AssetType


def get_user_account(
    session: Session,
    user_account_id: int,
) -> UserAccount:
    account: Optional[UserAccount] = (
        session.query(UserAccount)
        .filter_by(
            id=user_account_id,
        )
        .first()
    )
    if not account:
        raise ResourceNotFoundError(f"user account '{user_account_id}' not found")
    return account


def find_user_account_by_email(session: Session, email: str) -> Optional[UserAccount]:
    return session.query(UserAccount).filter_by(email=email).first()


def get_user_account_settings(
    session: Session,
    user_account_id: int,
) -> UserAccountSettings:
    settings: Optional[UserAccountSettings] = (
        session.query(UserAccountSettings)
        .filter_by(
            user_account_id=user_account_id,
        )
        .first()
    )
    if not settings:
        raise ResourceNotFoundError(f"user account '{user_account_id}' not found")
    return settings


def find_provider(
    session: Session,
    provider_id: str,
) -> Optional[Provider]:
    return session.query(Provider).filter_by(id=provider_id).first()


def get_provider(
    session: Session,
    provider_id: str,
) -> Provider:
    provider = find_provider(session, provider_id)
    if not provider:
        raise ResourceNotFoundError(f"provider '{provider_id}' not found")
    return provider


def linked_account_exists(
    session: Session,
    user_account_id: int,
    account_name: str,
) -> bool:
    return (
        session.query(LinkedAccount)
        .filter_by(user_account_id=user_account_id)
        .filter_by(account_name=account_name)
        .count()
    ) > 0


def find_linked_accounts(
    session: Session,
    user_account_id: int,
) -> list[LinkedAccount]:
    results: list[LinkedAccount] = (
        session.query(LinkedAccount)
        .filter_by(user_account_id=user_account_id)
        .filter_by(deleted=False)
        .options(joinedload(LinkedAccount.provider))
        .all()
    )
    return results


def get_last_history_entry(
    session: Session,
    user_account_id: int,
) -> UserAccountHistoryEntry:
    entry: Optional[UserAccountHistoryEntry] = (
        session.query(UserAccountHistoryEntry)
        .filter_by(user_account_id=user_account_id)
        .filter_by(available=True)
        .order_by(desc(UserAccountHistoryEntry.effective_at))
        .first()
    )
    if entry is None:
        raise MissingUserData("No valuation available for this account")
    return entry


@dataclass
class HistoricalValuationEntry:
    valuation_period: Union[date, str]
    period_start: datetime
    period_end: datetime
    first_value: float
    last_value: float
    abs_change: float
    rel_change: float
    min_value: float
    max_value: float


class ValuationGrouping(Protocol):
    datatype: str
    sql_grouping: str


class DailyValuationGrouping(ValuationGrouping):
    datatype = "datetime"
    sql_grouping = "fuahe.effective_at::timestamp::date"


class WeeklyValuationGrouping(ValuationGrouping):
    datatype = "category"
    sql_grouping = "'W' || to_char(fuahe.effective_at, 'IW IYYY')"


class MonthlyValuationGrouping(ValuationGrouping):
    datatype = "category"
    sql_grouping = "to_char(fuahe.effective_at, 'Month YYYY')"


class QuarterlyValuationGrouping(ValuationGrouping):
    datatype = "category"
    sql_grouping = "'Q' || to_char(fuahe.effective_at, 'Q YYYY')"


class YearlyValuationGrouping(ValuationGrouping):
    datatype = "category"
    sql_grouping = "extract(year from fuahe.effective_at)::text"


def _get_valuation_grouping_from_frequency(
    frequency: ValuationFrequency,
) -> Type[ValuationGrouping]:
    return {
        ValuationFrequency.Daily: DailyValuationGrouping,
        ValuationFrequency.Weekly: WeeklyValuationGrouping,
        ValuationFrequency.Monthly: MonthlyValuationGrouping,
        ValuationFrequency.Quarterly: QuarterlyValuationGrouping,
        ValuationFrequency.Yearly: YearlyValuationGrouping,
    }[frequency]


def get_user_account_historical_valuation(
    session: Session,
    user_account_id: int,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    frequency: Optional[ValuationFrequency] = None,
) -> list[HistoricalValuationEntry]:
    frequency = frequency or ValuationFrequency.Daily
    grouping = _get_valuation_grouping_from_frequency(frequency).sql_grouping
    query_params: dict[str, Any] = {"user_account_id": user_account_id}
    main_query = f"""
        select distinct on ({grouping}) {grouping} as valuation_period,
               first_value(fuahe.effective_at) over (
                   partition by {grouping}
                   order by fuahe.effective_at
               ) as period_start,
               first_value(fuahe.effective_at) over (
                   partition by {grouping}
                   order by fuahe.effective_at desc
               ) as period_end,
               first_value(fuavhe.valuation) over (
                   partition by {grouping}
                   order by fuahe.effective_at
               ) as first_value,
               first_value(fuavhe.valuation) over (
                   partition by {grouping}
                   order by fuahe.effective_at desc
               ) as last_value,
               min(fuavhe.valuation) over (
                   partition by {grouping}
               ) as min_value,
               max(fuavhe.valuation) over (
                   partition by {grouping}
               ) as max_value
        from finbot_user_accounts_valuation_history_entries fuavhe
                 join finbot_user_accounts_history_entries fuahe
                   on fuavhe.history_entry_id = fuahe.id
        where fuahe.user_account_id = :user_account_id
          and fuahe.available
    """
    if from_time:
        query_params["from_time"] = from_time
        main_query += " and fuahe.effective_at >= :from_time "
    if to_time:
        query_params["to_time"] = to_time
        main_query += " and fuahe.effective_at <= :to_time "
    query = f"""
        select q.*,
               (q.last_value - q.first_value) as abs_change,
               case q.first_value
                when 0.0 then null
                else (q.last_value - q.first_value) / (q.first_value)
               end as rel_change
          from ({main_query}) q
      order by q.period_start
    """
    return [HistoricalValuationEntry(**row_to_dict(row)) for row in session.execute(text(query), query_params)]


@dataclass
class LinkedAccountHistoricalValuationEntry(HistoricalValuationEntry):
    linked_account_id: int
    linked_account_name: str


def get_historical_valuation_by_linked_account(
    session: Session,
    user_account_id: int,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    frequency: Optional[ValuationFrequency] = None,
) -> list[LinkedAccountHistoricalValuationEntry]:
    frequency = frequency or ValuationFrequency.Daily
    sub_grouping = _get_valuation_grouping_from_frequency(frequency).sql_grouping
    query_params: dict[str, Any] = {"user_account_id": user_account_id}
    main_query = f"""
        select distinct on (flavhe.linked_account_id, {sub_grouping})
               flavhe.linked_account_id as linked_account_id,
               fla.account_name as linked_account_name,
               {sub_grouping} as valuation_period,
               first_value(fuahe.effective_at) over (
                   partition by flavhe.linked_account_id, {sub_grouping}
                   order by fuahe.effective_at
               ) as period_start,
               first_value(fuahe.effective_at) over (
                   partition by flavhe.linked_account_id, {sub_grouping}
                   order by fuahe.effective_at desc
               ) as period_end,
               first_value(flavhe.valuation) over (
                   partition by flavhe.linked_account_id, {sub_grouping}
                   order by fuahe.effective_at
               ) as first_value,
               first_value(flavhe.valuation) over (
                   partition by flavhe.linked_account_id, {sub_grouping}
                   order by fuahe.effective_at desc
               ) as last_value,
               min(flavhe.valuation) over (
                   partition by flavhe.linked_account_id, {sub_grouping}
               ) as min_value,
               max(flavhe.valuation) over (
                   partition by flavhe.linked_account_id, {sub_grouping}
               ) as max_value
          from finbot_linked_accounts_valuation_history_entries flavhe
          join finbot_user_accounts_history_entries fuahe
            on flavhe.history_entry_id = fuahe.id
          join finbot_linked_accounts fla
            on flavhe.linked_account_id = fla.id
         where fuahe.user_account_id = :user_account_id
           and fuahe.available
           and not fla.deleted
    """
    if from_time:
        query_params["from_time"] = from_time
        main_query += " and fuahe.effective_at >= :from_time "
    if to_time:
        query_params["to_time"] = to_time
        main_query += " and fuahe.effective_at <= :to_time "
    query = f"""
        select q.*,
               (q.last_value - q.first_value) as abs_change,
               case q.first_value
                when 0 then null
                else (q.last_value - q.first_value) / (q.first_value)
               end as rel_change
          from ({main_query}) q
      order by q.period_start, q.linked_account_id
    """
    return [
        LinkedAccountHistoricalValuationEntry(**row_to_dict(row)) for row in session.execute(text(query), query_params)
    ]


@dataclass
class AssetTypeHistoricalValuationEntry(HistoricalValuationEntry):
    asset_type: AssetType
    asset_class: AssetClass


class HistoricalValuationByAssetType(object):
    agg_criterion = "fsaivhe.asset_type || ';' || fsaivhe.asset_class"

    @staticmethod
    def parse_row(row: dict[str, Any]) -> AssetTypeHistoricalValuationEntry:
        raw_asset_type, raw_asset_class = row["agg_criterion"].split(";")
        del row["agg_criterion"]
        row["asset_type"] = AssetType[raw_asset_type]
        row["asset_class"] = AssetClass[raw_asset_class]
        return AssetTypeHistoricalValuationEntry(**row)


@dataclass
class AssetClassHistoricalValuationEntry(HistoricalValuationEntry):
    asset_class: AssetClass


class HistoricalValuationByAssetClass(object):
    agg_criterion = "fsaivhe.asset_class"

    @staticmethod
    def parse_row(row: dict[str, Any]) -> AssetClassHistoricalValuationEntry:
        raw_asset_class = row["agg_criterion"]
        del row["agg_criterion"]
        row["asset_class"] = AssetClass[raw_asset_class]
        return AssetClassHistoricalValuationEntry(**row)


@overload
def get_historical_valuation_by(
    session: Session,
    user_account_id: int,
    by: type[HistoricalValuationByAssetType],
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    frequency: Optional[ValuationFrequency] = None,
) -> list[AssetTypeHistoricalValuationEntry]: ...


@overload
def get_historical_valuation_by(
    session: Session,
    user_account_id: int,
    by: type[HistoricalValuationByAssetClass],
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    frequency: Optional[ValuationFrequency] = None,
) -> list[AssetClassHistoricalValuationEntry]: ...


def get_historical_valuation_by(
    session: Session,
    user_account_id: int,
    by: type[HistoricalValuationByAssetType] | type[HistoricalValuationByAssetClass],
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    frequency: Optional[ValuationFrequency] = None,
) -> list[AssetTypeHistoricalValuationEntry] | list[AssetClassHistoricalValuationEntry]:
    frequency = frequency or ValuationFrequency.Daily
    sub_grouping = _get_valuation_grouping_from_frequency(frequency).sql_grouping
    query_params: dict[str, Any] = {"user_account_id": user_account_id}
    time_clause = ""
    if from_time:
        query_params["from_time"] = from_time
        time_clause += " and fuahe.effective_at >= :from_time "
    if to_time:
        query_params["to_time"] = to_time
        time_clause += " and fuahe.effective_at <= :to_time "
    main_query = f"""
        select distinct on (agg_items.agg_criterion, {sub_grouping})
               {sub_grouping} as valuation_period,
               agg_items.agg_criterion,
               first_value(fuahe.effective_at) over (
                   partition by agg_items.agg_criterion, {sub_grouping}
                   order by fuahe.effective_at
                ) as period_start,
               first_value(fuahe.effective_at) over (
                   partition by agg_items.agg_criterion, {sub_grouping}
                   order by fuahe.effective_at desc
                ) as period_end,
               first_value(agg_items.valuation) over (
                   partition by agg_items.agg_criterion, {sub_grouping}
                   order by fuahe.effective_at
                ) as first_value,
               first_value(agg_items.valuation) over (
                   partition by agg_items.agg_criterion, {sub_grouping}
                   order by fuahe.effective_at desc
               ) as last_value,
               min(agg_items.valuation) over (
                   partition by agg_items.agg_criterion, {sub_grouping}
               ) as max_value,
               min(agg_items.valuation) over (
                   partition by agg_items.agg_criterion, {sub_grouping}
               ) as min_value
          from (
              select fsaivhe.history_entry_id,
                     {by.agg_criterion} as agg_criterion,
                     sum(valuation) as valuation
                from finbot_sub_accounts_items_valuation_history_entries fsaivhe
                join finbot_user_accounts_history_entries fuahe
                  on fsaivhe.history_entry_id = fuahe.id
                join finbot_linked_accounts fla
                  on fsaivhe.linked_account_id = fla.id
               where fuahe.available
             and not fla.deleted
                 and fuahe.user_account_id = :user_account_id {time_clause}
                 and fsaivhe.item_type = 'Asset'
            group by history_entry_id, {by.agg_criterion}
          ) agg_items
          join finbot_user_accounts_history_entries fuahe on agg_items.history_entry_id = fuahe.id
    """
    query = f"""
        select q.*,
               (q.last_value - q.first_value) as abs_change,
               case q.first_value
                when 0 then null
                else (q.last_value - q.first_value) / (q.first_value)
               end as rel_change
          from ({main_query}) q
      order by q.period_start, q.agg_criterion
    """
    return [  # type: ignore
        by.parse_row(row_to_dict(row)) for row in session.execute(text(query), query_params)
    ]


def find_snapshot_linked_account_errors(
    session: Session,
    snapshot_id: int,
) -> list[LinkedAccountSnapshotEntry]:
    return cast(
        list[LinkedAccountSnapshotEntry],
        session.query(LinkedAccountSnapshotEntry)
        .filter_by(snapshot_id=snapshot_id)
        .filter_by(success=False)
        .options(joinedload(LinkedAccountSnapshotEntry.linked_account))
        .all(),
    )


class LinkedAccountStatus(TypedDict):
    status: Literal["stable", "unstable"]
    errors: list[Any] | None
    last_snapshot_id: int
    last_snapshot_time: datetime


def get_linked_accounts_statuses(
    session: Session, user_account_id: int, linked_account_ids: set[int] | None = None
) -> dict[int, LinkedAccountStatus]:
    linked_account_ids_filter = None
    if linked_account_ids:
        assert all(isinstance(linked_account_id, int) for linked_account_id in linked_account_ids)
        linked_account_ids_filter = f"linked_account_id IN ({', '.join(str(entry) for entry in linked_account_ids)})"
    query = f"""
        select linked_account_id,
               snapshot_id,
               success,
               failure_details,
               created_at as snapshot_time
          from finbot_linked_accounts_snapshots
         where (linked_account_id, created_at) in (
             select linked_account_id, max(created_at)
               from finbot_linked_accounts_snapshots
              where linked_account_id in (
                  select id
                    from finbot_linked_accounts
                    where user_account_id = :user_account_id
                      and not deleted and {linked_account_ids_filter or "1 = 1"}
              )
           group by linked_account_id
        )
    """
    query_params = {"user_account_id": user_account_id}
    results: dict[int, LinkedAccountStatus] = {}
    for row in session.execute(text(query), query_params):
        data = row_to_dict(row)
        success = data["success"]
        raw_failure_details = data["failure_details"]
        results[data["linked_account_id"]] = {
            "status": "stable" if success else "unstable",
            "errors": json.loads(raw_failure_details) if raw_failure_details else [],
            "last_snapshot_id": data["snapshot_id"],
            "last_snapshot_time": data["snapshot_time"],
        }
    return results


def get_linked_account_status(
    session: Session, user_account_id: int, linked_account_id: int
) -> LinkedAccountStatus | None:
    return get_linked_accounts_statuses(
        session=session,
        user_account_id=user_account_id,
        linked_account_ids={linked_account_id},
    ).get(linked_account_id)


def get_user_account_valuation(
    session: Session,
    history_entry_id: int,
) -> UserAccountValuationHistoryEntry:
    entry: UserAccountValuationHistoryEntry = (
        session.query(UserAccountValuationHistoryEntry)
        .filter_by(history_entry_id=history_entry_id)
        .options(joinedload(UserAccountValuationHistoryEntry.valuation_change))
        .options(joinedload(UserAccountValuationHistoryEntry.account_valuation_history_entry))
        .one()
    )
    return entry


def find_linked_accounts_valuation(
    session: Session,
    history_entry_id: int,
) -> list[LinkedAccountValuationHistoryEntry]:
    entries: list[LinkedAccountValuationHistoryEntry] = (
        session.query(LinkedAccountValuationHistoryEntry)
        .filter_by(history_entry_id=history_entry_id)
        .options(joinedload(LinkedAccountValuationHistoryEntry.valuation_change))
        .options(joinedload(LinkedAccountValuationHistoryEntry.linked_account))
        .options(joinedload(LinkedAccountValuationHistoryEntry.effective_snapshot))
        .all()
    )
    return entries


def find_sub_accounts_valuation(
    session: Session,
    history_entry_id: int,
    linked_account_id: Optional[int] = None,
) -> list[SubAccountValuationHistoryEntry]:
    query = session.query(SubAccountValuationHistoryEntry).filter_by(
        history_entry_id=history_entry_id,
    )
    if linked_account_id is not None:
        query = query.filter_by(linked_account_id=linked_account_id)
    query = query.options(joinedload(SubAccountValuationHistoryEntry.valuation_change))
    return query.all()


def find_items_valuation(
    session: Session,
    history_entry_id: int,
    linked_account_id: Optional[int] = None,
    sub_account_id: Optional[str] = None,
) -> list[SubAccountItemValuationHistoryEntry]:
    query = session.query(SubAccountItemValuationHistoryEntry).filter_by(
        history_entry_id=history_entry_id,
    )
    if linked_account_id is not None:
        query = query.filter_by(linked_account_id=linked_account_id)
    if sub_account_id is not None:
        query = query.filter_by(sub_account_id=sub_account_id)
    query = query.options(joinedload(SubAccountItemValuationHistoryEntry.valuation_change))
    return query.all()


def get_linked_account(
    session: Session,
    user_account_id: int,
    linked_account_id: int,
) -> LinkedAccount:
    linked_account: Optional[LinkedAccount] = (
        session.query(LinkedAccount)
        .filter_by(
            id=linked_account_id,
        )
        .filter_by(
            user_account_id=user_account_id,
        )
        .first()
    )
    if not linked_account:
        raise ResourceNotFoundError(f"linked account {linked_account} not found")
    return linked_account
