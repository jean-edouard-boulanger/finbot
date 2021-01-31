from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload

from finbot.apps.appwsrv.exceptions import ApplicationError
from finbot.apps.appwsrv import timeseries
from finbot.core import utils
from finbot.model import (
    LinkedAccount,
    Provider,
    UserAccount,
    UserAccountHistoryEntry,
    UserAccountValuationHistoryEntry,
    LinkedAccountValuationHistoryEntry,
    SubAccountValuationHistoryEntry,
    SubAccountItemValuationHistoryEntry
)


def get_user_account(session, user_account_id: int) -> UserAccount:
    account = (session.query(UserAccount)
                      .filter_by(id=user_account_id)
                      .options(joinedload(UserAccount.settings))
                      .first())
    if not account:
        raise ApplicationError(f"user account '{user_account_id}' not found")
    return account


def find_provider(session, provider_id: str) -> Provider:
    return session.query(Provider).filter_by(id=provider_id).first()


def find_linked_accounts(session, user_account_id: int) -> List[LinkedAccount]:
    return (session.query(LinkedAccount)
                   .filter_by(user_account_id=user_account_id)
                   .filter_by(deleted=False)
                   .options(joinedload(LinkedAccount.provider))
                   .all())


def find_last_history_entry(session,
                            user_account_id: int) -> UserAccountHistoryEntry:
    return (session.query(UserAccountHistoryEntry)
                   .filter_by(user_account_id=user_account_id)
                   .filter_by(available=True)
                   .order_by(desc(UserAccountHistoryEntry.effective_at))
                   .first())


def find_user_account_historical_valuation(session,
                                           user_account_id: int,
                                           from_time: datetime,
                                           to_time: datetime) -> List[UserAccountHistoryEntry]:
    return (session.query(UserAccountHistoryEntry)
                   .filter_by(user_account_id=user_account_id)
                   .filter_by(available=True)
                   .filter(UserAccountHistoryEntry.effective_at >= from_time)
                   .filter(UserAccountHistoryEntry.effective_at <= to_time)
                   .order_by(asc(UserAccountHistoryEntry.effective_at))
                   .options(joinedload(UserAccountHistoryEntry.user_account_valuation_history_entry))
                   .all())


def find_linked_accounts_historical_valuation(session,
                                              user_account_id: int,
                                              from_time: datetime,
                                              to_time: datetime) -> Dict[int, List[LinkedAccountValuationHistoryEntry]]:
    history_entries = (session.query(UserAccountHistoryEntry)
                              .filter_by(user_account_id=user_account_id)
                              .filter_by(available=True)
                              .filter(UserAccountHistoryEntry.effective_at >= from_time)
                              .filter(UserAccountHistoryEntry.effective_at <= to_time)
                              .order_by(asc(UserAccountHistoryEntry.effective_at))
                              .options(joinedload(UserAccountHistoryEntry.linked_accounts_valuation_history_entries))
                              .all())
    results = defaultdict(list)
    history_entry: UserAccountHistoryEntry
    for history_entry in history_entries:
        valuation: LinkedAccountValuationHistoryEntry
        for valuation in history_entry.linked_accounts_valuation_history_entries:
            results[valuation.linked_account_id].append(valuation)
    return results


def find_user_account_valuation(session,
                                history_entry_id: int) -> UserAccountValuationHistoryEntry:
    return (session.query(UserAccountValuationHistoryEntry)
                   .filter_by(history_entry_id=history_entry_id)
                   .options(joinedload(UserAccountValuationHistoryEntry.valuation_change))
                   .options(joinedload(UserAccountValuationHistoryEntry.account_valuation_history_entry))
                   .one())


def find_linked_accounts_valuation(session,
                                   history_entry_id: int) -> List[LinkedAccountValuationHistoryEntry]:
    return (session.query(LinkedAccountValuationHistoryEntry)
                   .filter_by(history_entry_id=history_entry_id)
                   .options(joinedload(LinkedAccountValuationHistoryEntry.valuation_change))
                   .options(joinedload(LinkedAccountValuationHistoryEntry.linked_account))
                   .options(joinedload(LinkedAccountValuationHistoryEntry.effective_snapshot))
                   .all())


def find_sub_accounts_valuation(session,
                                history_entry_id: int,
                                linked_account_id: Optional[int] = None) -> List[SubAccountValuationHistoryEntry]:
    query = (session.query(SubAccountValuationHistoryEntry)
                    .filter_by(history_entry_id=history_entry_id))
    if linked_account_id is not None:
        query = query.filter_by(linked_account_id=linked_account_id)
    query = query.options(joinedload(SubAccountValuationHistoryEntry.valuation_change))
    return query.all()


def find_items_valuation(session,
                         history_entry_id: int,
                         linked_account_id: Optional[int] = None,
                         sub_account_id: Optional[str] = None) -> List[SubAccountItemValuationHistoryEntry]:
    query = (session.query(SubAccountItemValuationHistoryEntry)
                    .filter_by(history_entry_id=history_entry_id))
    if linked_account_id is not None:
        query = query.filter_by(linked_account_id=linked_account_id)
    if sub_account_id is not None:
        query = query.filter_by(sub_account_id=sub_account_id)
    query = query.options(joinedload(SubAccountItemValuationHistoryEntry.valuation_change))
    return query.all()


def find_linked_account(session, user_account_id: int, linked_account_id: int) -> LinkedAccount:
    return (session.query(LinkedAccount)
                   .filter_by(id=linked_account_id)
                   .filter_by(user_account_id=user_account_id)
                   .first())


def get_holdings_report(session, history_entry: UserAccountHistoryEntry):
    user_account_valuation = find_user_account_valuation(session, history_entry.id)
    linked_accounts_valuation = find_linked_accounts_valuation(session, history_entry.id)
    sub_accounts_valuation = find_sub_accounts_valuation(session, history_entry.id)
    mapped_sub_accounts: Dict[int, List[SubAccountValuationHistoryEntry]] = defaultdict(list)
    for sub_account in sub_accounts_valuation:
        mapped_sub_accounts[sub_account.linked_account_id].append(sub_account)
    items_valuation = find_items_valuation(session, history_entry.id)
    mapped_items: Dict[Tuple[int, str], List[SubAccountItemValuationHistoryEntry]] = defaultdict(list)
    for item in items_valuation:
        mapped_items[(item.linked_account_id, item.sub_account_id)].append(item)

    to_time = utils.now_utc()
    from_time = to_time - timedelta(days=30)
    user_account_historical_valuation = find_user_account_historical_valuation(
        session=session,
        user_account_id=history_entry.user_account_id,
        from_time=from_time,
        to_time=to_time)
    historical_valuation_by_account = find_linked_accounts_historical_valuation(
        session=session,
        user_account_id=history_entry.user_account_id,
        from_time=from_time,
        to_time=to_time)
    sparkline_schedule = timeseries.create_schedule(
        from_time=from_time,
        to_time=to_time,
        frequency=timeseries.ScheduleFrequency.Daily)

    account_valuation_history_entry = user_account_valuation.account_valuation_history_entry
    valuation_currency = account_valuation_history_entry.valuation_ccy

    valuation_tree = {
        "role": "user_account",
        "valuation": {
            "currency": valuation_currency,
            "value": user_account_valuation.valuation,
            "change": user_account_valuation.valuation_change,
            "sparkline": [
                uas_v.user_account_valuation_history_entry.valuation
                if uas_v is not None else None
                for valuation_time, uas_v in timeseries.schedulify(
                    sparkline_schedule,
                    user_account_historical_valuation,
                    lambda uas_v: uas_v.effective_at)
            ]
        },
        "children": [
            {
                "role": "linked_account",
                "linked_account": {
                    "id": la_v.linked_account_id,
                    "provider_id": la_v.linked_account.provider_id,
                    "description": la_v.linked_account.account_name,
                },
                "valuation": {
                    "currency": valuation_currency,
                    "value": la_v.valuation,
                    "change": la_v.valuation_change,
                    "sparkline": [
                        las_v.valuation if las_v is not None else None
                        for valuation_time, las_v in timeseries.schedulify(
                            sparkline_schedule,
                            historical_valuation_by_account.get(la_v.linked_account_id),
                            lambda las_v: las_v.account_valuation_history_entry.effective_at)
                    ]
                },
                "children": [
                    {
                        "role": "sub_account",
                        "sub_account": {
                            "id": sa_v.sub_account_id,
                            "currency": sa_v.sub_account_ccy,
                            "description": sa_v.sub_account_description,
                            "type": sa_v.sub_account_type
                        },
                        "valuation": {
                            "value": sa_v.valuation,
                            "value_account_currency": sa_v.valuation_sub_account_ccy,
                            "change": sa_v.valuation_change,
                            "total_liabilities": sa_v.total_liabilities,
                            "currency": valuation_currency,
                        },
                        "children": [
                            {
                                "role": "item",
                                "item": {
                                    "name": item_v.name,
                                    "type": item_v.item_type.name,
                                    "sub_type": item_v.item_subtype,
                                },
                                "valuation": {
                                    "units": item_v.units,
                                    "value": item_v.valuation,
                                    "value_account_currency": item_v.valuation_sub_account_ccy,
                                    "change": item_v.valuation_change,
                                    "currency": valuation_currency
                                },
                                "children": [
                                    {
                                        "role": "metadata",
                                        "label": key,
                                        "value": value
                                    }
                                    for (key, value) in [
                                        (f"Units",
                                         f"{item_v.units:.2f}" if item_v.units else None),
                                        (f"Value ({sa_v.sub_account_ccy})",
                                         f"{item_v.valuation_sub_account_ccy:.2f}"),
                                        (f"Unit value ({sa_v.sub_account_ccy})",
                                         f"{sa_v.valuation_sub_account_ccy / item_v.units:.2f}" if item_v.units else None),
                                        (f"Type", item_v.item_subtype),
                                        (f"Account currency", sa_v.sub_account_ccy)
                                    ]
                                    if value is not None
                                ]
                            }
                            for item_v in mapped_items.get((sa_v.linked_account_id, sa_v.sub_account_id), [])
                        ]
                    }
                    for sa_v in mapped_sub_accounts.get(la_v.linked_account_id, [])
                ]
            }
            for la_v in linked_accounts_valuation
            if not la_v.linked_account.deleted
        ]
    }

    return {
        "valuation_tree": valuation_tree
    }
