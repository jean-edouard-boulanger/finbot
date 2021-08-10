from finbot.core.errors import InvalidUserInput
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

from collections import defaultdict
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload
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


def find_provider(session, provider_id: str) -> Provider:
    return session.query(Provider).filter_by(id=provider_id).first()


def find_linked_accounts(session, user_account_id: int) -> list[LinkedAccount]:
    return (
        session.query(LinkedAccount)
        .filter_by(user_account_id=user_account_id)
        .filter_by(deleted=False)
        .options(joinedload(LinkedAccount.provider))
        .all()
    )


def find_last_history_entry(session, user_account_id: int) -> UserAccountHistoryEntry:
    return (
        session.query(UserAccountHistoryEntry)
        .filter_by(user_account_id=user_account_id)
        .filter_by(available=True)
        .order_by(desc(UserAccountHistoryEntry.effective_at))
        .first()
    )


def find_user_account_historical_valuation(
    session, user_account_id: int, from_time: datetime, to_time: datetime
) -> list[UserAccountHistoryEntry]:
    return (
        session.query(UserAccountHistoryEntry)
        .filter_by(user_account_id=user_account_id)
        .filter_by(available=True)
        .filter(UserAccountHistoryEntry.effective_at >= from_time)
        .filter(UserAccountHistoryEntry.effective_at <= to_time)
        .order_by(asc(UserAccountHistoryEntry.effective_at))
        .options(
            joinedload(UserAccountHistoryEntry.user_account_valuation_history_entry)
        )
        .all()
    )


def find_linked_accounts_historical_valuation(
    session, user_account_id: int, from_time: datetime, to_time: datetime
) -> dict[int, list[LinkedAccountValuationHistoryEntry]]:
    history_entries = (
        session.query(UserAccountHistoryEntry)
        .filter_by(user_account_id=user_account_id)
        .filter_by(available=True)
        .filter(UserAccountHistoryEntry.effective_at >= from_time)
        .filter(UserAccountHistoryEntry.effective_at <= to_time)
        .order_by(asc(UserAccountHistoryEntry.effective_at))
        .options(
            joinedload(
                UserAccountHistoryEntry.linked_accounts_valuation_history_entries
            )
        )
        .all()
    )
    results = defaultdict(list)
    history_entry: UserAccountHistoryEntry
    for history_entry in history_entries:
        valuation: LinkedAccountValuationHistoryEntry
        for valuation in history_entry.linked_accounts_valuation_history_entries:
            results[valuation.linked_account_id].append(valuation)
    return results


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


def find_user_account_valuation(
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
