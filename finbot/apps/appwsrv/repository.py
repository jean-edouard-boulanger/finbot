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


def get_linked_account(session, user_account_id: int, linked_account_id: int) -> LinkedAccount:
    linked_account = (session.query(LinkedAccount)
                             .filter_by(id=linked_account_id)
                             .filter_by(user_account_id=user_account_id)
                             .first())
    if not linked_account:
        raise ApplicationError(f"linked account {linked_account} not found")
    return linked_account
