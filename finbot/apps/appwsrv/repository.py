from typing import List
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from finbot.model import (
    LinkedAccount,
    UserAccountHistoryEntry,
    SubAccountValuationHistoryEntry
)


def find_last_history_entry(session,
                            user_account_id: int) -> UserAccountHistoryEntry:
    return (session.query(UserAccountHistoryEntry)
                   .filter_by(user_account_id=user_account_id)
                   .filter_by(available=True)
                   .order_by(desc(UserAccountHistoryEntry.effective_at))
                   .first())


def find_sub_accounts_history_entries(session,
                                      history_entry_id: int,
                                      linked_account_id: int) -> List[SubAccountValuationHistoryEntry]:
    return (session.query(SubAccountValuationHistoryEntry)
                   .filter_by(history_entry_id=history_entry_id)
                   .filter_by(linked_account_id=linked_account_id)
                   .options(joinedload(SubAccountValuationHistoryEntry.valuation_change))
                   .all())


def find_linked_account(session, linked_account_id: int) -> LinkedAccount:
    return session.query(LinkedAccount).filter_by(id=linked_account_id).first()
