from finbot.core.errors import InvalidUserInput, MissingUserData
from finbot.model import (
    LinkedAccount,
    Provider,
    UserAccount,
    UserAccountSettings,
    UserAccountSnapshot,
    LinkedAccountSnapshotEntry,
    UserAccountPlaidSettings,
    UserAccountHistoryEntry,
    UserAccountValuationHistoryEntry,
    LinkedAccountValuationHistoryEntry,
    SnapshotStatus,
    SubAccountValuationHistoryEntry,
    SubAccountItemValuationHistoryEntry,
)

from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from typing import Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, date
import enum
import logging


logger = logging.getLogger()


def get_user_account(session, user_account_id: int) -> UserAccount:
    account = session.query(UserAccount).filter_by(id=user_account_id).first()
    if not account:
        raise InvalidUserInput(f"user account '{user_account_id}' not found")
    return account


def get_user_account_settings(session, user_account_id: int) -> UserAccountSettings:
    settings = (
        session.query(UserAccountSettings)
        .filter_by(user_account_id=user_account_id)
        .first()
    )
    if not settings:
        raise InvalidUserInput(f"user account '{user_account_id}' not found")
    return settings


def get_user_account_plaid_settings(
    session, user_account_id: int
) -> Optional[UserAccountPlaidSettings]:
    return (
        session.query(UserAccountPlaidSettings)
        .filter_by(user_account_id=user_account_id)
        .first()
    )


def find_provider(session, provider_id: str) -> Optional[Provider]:
    return session.query(Provider).filter_by(id=provider_id).first()


def get_provider(session, provider_id: str) -> Provider:
    provider = find_provider(session, provider_id)
    if not provider:
        raise InvalidUserInput(f"provider '{provider_id}' not found")
    return provider


def linked_account_exists(session, user_account_id: int, account_name: str) -> bool:
    return (
        session.query(LinkedAccount)
        .filter_by(user_account_id=user_account_id)
        .filter_by(account_name=account_name)
        .count()
    ) > 0


def find_linked_accounts(session, user_account_id: int) -> list[LinkedAccount]:
    return (
        session.query(LinkedAccount)
        .filter_by(user_account_id=user_account_id)
        .filter_by(deleted=False)
        .options(joinedload(LinkedAccount.provider))
        .all()
    )


def get_last_history_entry(session, user_account_id: int) -> UserAccountHistoryEntry:
    entry = (
        session.query(UserAccountHistoryEntry)
        .filter_by(user_account_id=user_account_id)
        .filter_by(available=True)
        .order_by(desc(UserAccountHistoryEntry.effective_at))
        .first()
    )
    if entry is None:
        raise MissingUserData("No valuation available for this account")
    return entry


class ValuationFrequency(enum.Enum):
    Daily = enum.auto()
    Weekly = enum.auto()
    Monthly = enum.auto()
    Quarterly = enum.auto()
    Yearly = enum.auto()

    def serialize(self) -> str:
        return self.name.lower()

    @staticmethod
    def deserialize(data: str):
        return {
            "daily": ValuationFrequency.Daily,
            "weekly": ValuationFrequency.Weekly,
            "monthly": ValuationFrequency.Monthly,
            "quarterly": ValuationFrequency.Quarterly,
            "yearly": ValuationFrequency.Yearly,
        }[data.lower()]


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


class DailyValuationGrouping(object):
    datatype = "datetime"
    sql_grouping = "fuahe.effective_at::timestamp::date"


class WeeklyValuationGrouping(object):
    datatype = "category"
    sql_grouping = (
        "'W' || extract(week from fuahe.effective_at)::text "
        "|| ' ' || extract(year from fuahe.effective_at)::text"
    )


class MonthlyValuationGrouping(object):
    datatype = "category"
    sql_grouping = (
        "to_char(fuahe.effective_at, 'Mon') "
        "|| ' ' || extract(year from fuahe.effective_at)::text"
    )


class QuarterlyValuationGrouping(object):
    datatype = "category"
    sql_grouping = (
        "'Q' || extract(quarter from fuahe.effective_at) "
        "|| ' ' || extract(year from fuahe.effective_at)::text"
    )


class YearlyValuationGrouping(object):
    datatype = "category"
    sql_grouping = "extract(year from fuahe.effective_at)::text"


def _get_valuation_grouping_from_frequency(frequency: ValuationFrequency):
    return {
        ValuationFrequency.Daily: DailyValuationGrouping,
        ValuationFrequency.Weekly: WeeklyValuationGrouping,
        ValuationFrequency.Monthly: MonthlyValuationGrouping,
        ValuationFrequency.Quarterly: QuarterlyValuationGrouping,
        ValuationFrequency.Yearly: YearlyValuationGrouping,
    }[frequency]()


def get_user_account_historical_valuation(
    session,
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
    return [
        HistoricalValuationEntry(**row) for row in session.execute(query, query_params)
    ]


@dataclass
class LinkedAccountHistoricalValuationEntry(HistoricalValuationEntry):
    linked_account_id: int
    linked_account_name: str


def get_historical_valuation_by_linked_account(
    session,
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
        LinkedAccountHistoricalValuationEntry(**row)
        for row in session.execute(query, query_params)
    ]


@dataclass
class AssetTypeHistoricalValuationEntry(HistoricalValuationEntry):
    asset_type: str


def get_historical_valuation_by_asset_type(
    session,
    user_account_id: int,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    frequency: Optional[ValuationFrequency] = None,
) -> list[AssetTypeHistoricalValuationEntry]:
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
        select distinct on (agg_items.asset_type, {sub_grouping})
               {sub_grouping} as valuation_period,
               agg_items.asset_type,
               first_value(fuahe.effective_at) over (
                   partition by agg_items.asset_type, {sub_grouping}
                   order by fuahe.effective_at
                ) as period_start,
               first_value(fuahe.effective_at) over (
                   partition by agg_items.asset_type, {sub_grouping}
                   order by fuahe.effective_at desc
                ) as period_end,
               first_value(agg_items.valuation) over (
                   partition by agg_items.asset_type, {sub_grouping}
                   order by fuahe.effective_at
                ) as first_value,
               first_value(agg_items.valuation) over (
                   partition by agg_items.asset_type, {sub_grouping}
                   order by fuahe.effective_at desc
               ) as last_value,
               min(agg_items.valuation) over (
                   partition by agg_items.asset_type, {sub_grouping}
               ) as max_value,
               min(agg_items.valuation) over (
                   partition by agg_items.asset_type, {sub_grouping}
               ) as min_value
          from (
              select history_entry_id,
                     item_subtype as asset_type,
                     sum(valuation) as valuation
                from finbot_sub_accounts_items_valuation_history_entries fsaivhe
                join finbot_user_accounts_history_entries fuahe on fsaivhe.history_entry_id = fuahe.id
                join finbot_linked_accounts fla on fsaivhe.linked_account_id = fla.id
               where fuahe.available
             and not fla.deleted
                 and fuahe.user_account_id = :user_account_id {time_clause}
            group by history_entry_id, item_subtype
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
      order by q.period_start, q.asset_type
    """
    return [
        AssetTypeHistoricalValuationEntry(**row)
        for row in session.execute(query, query_params)
    ]


def get_linked_accounts_statuses(
    session, user_account_id: int
) -> dict[int, dict[str, Any]]:
    last_snapshot = (
        session.query(UserAccountSnapshot)
        .filter_by(user_account_id=user_account_id)
        .filter_by(status=SnapshotStatus.Success)
        .options(joinedload(UserAccountSnapshot.linked_accounts_entries))
        .order_by(desc(UserAccountSnapshot.start_time))
        .limit(1)
        .one_or_none()
    )
    output: dict[int, dict[str, Any]] = {}
    if not last_snapshot:
        return output
    entry: LinkedAccountSnapshotEntry
    for entry in last_snapshot.linked_accounts_entries:
        linked_account_id = entry.linked_account_id
        if linked_account_id is not None:
            if entry.success:
                output[linked_account_id] = {"status": "stable", "errors": None}
            else:
                output[linked_account_id] = {
                    "status": "unstable",
                    "errors": entry.failure_details,
                }
    return output


def get_linked_account_status(
    session, user_account_id: int, linked_account_id: int
) -> Optional[dict[str, Any]]:
    return get_linked_accounts_statuses(session, user_account_id).get(linked_account_id)


def get_user_account_valuation(
    session, history_entry_id: int
) -> UserAccountValuationHistoryEntry:
    return (
        session.query(UserAccountValuationHistoryEntry)
        .filter_by(history_entry_id=history_entry_id)
        .options(joinedload(UserAccountValuationHistoryEntry.valuation_change))
        .options(
            joinedload(UserAccountValuationHistoryEntry.account_valuation_history_entry)
        )
        .one()
    )


def find_linked_accounts_valuation(
    session, history_entry_id: int
) -> list[LinkedAccountValuationHistoryEntry]:
    return (
        session.query(LinkedAccountValuationHistoryEntry)
        .filter_by(history_entry_id=history_entry_id)
        .options(joinedload(LinkedAccountValuationHistoryEntry.valuation_change))
        .options(joinedload(LinkedAccountValuationHistoryEntry.linked_account))
        .options(joinedload(LinkedAccountValuationHistoryEntry.effective_snapshot))
        .all()
    )


def find_sub_accounts_valuation(
    session, history_entry_id: int, linked_account_id: Optional[int] = None
) -> list[SubAccountValuationHistoryEntry]:
    query = session.query(SubAccountValuationHistoryEntry).filter_by(
        history_entry_id=history_entry_id
    )
    if linked_account_id is not None:
        query = query.filter_by(linked_account_id=linked_account_id)
    query = query.options(joinedload(SubAccountValuationHistoryEntry.valuation_change))
    return query.all()


def find_items_valuation(
    session,
    history_entry_id: int,
    linked_account_id: Optional[int] = None,
    sub_account_id: Optional[str] = None,
) -> list[SubAccountItemValuationHistoryEntry]:
    query = session.query(SubAccountItemValuationHistoryEntry).filter_by(
        history_entry_id=history_entry_id
    )
    if linked_account_id is not None:
        query = query.filter_by(linked_account_id=linked_account_id)
    if sub_account_id is not None:
        query = query.filter_by(sub_account_id=sub_account_id)
    query = query.options(
        joinedload(SubAccountItemValuationHistoryEntry.valuation_change)
    )
    return query.all()


def get_linked_account(
    session, user_account_id: int, linked_account_id: int
) -> LinkedAccount:
    linked_account = (
        session.query(LinkedAccount)
        .filter_by(id=linked_account_id)
        .filter_by(user_account_id=user_account_id)
        .first()
    )
    if not linked_account:
        raise InvalidUserInput(f"linked account {linked_account} not found")
    return linked_account
