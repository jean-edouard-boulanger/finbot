from collections import defaultdict
from typing import List, Optional, Dict, Tuple
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from finbot.model import (
    LinkedAccount,
    Provider,
    UserAccountHistoryEntry,
    LinkedAccountValuationHistoryEntry,
    SubAccountValuationHistoryEntry,
    SubAccountItemValuationHistoryEntry
)


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


def load_valuation_tree(session, history_entry: UserAccountHistoryEntry):
    linked_accounts_valuation = find_linked_accounts_valuation(session, history_entry.id)
    sub_accounts_valuation = find_sub_accounts_valuation(session, history_entry.id)
    mapped_sub_accounts: Dict[int, List[SubAccountValuationHistoryEntry]] = defaultdict(list)
    for sub_account in sub_accounts_valuation:
        mapped_sub_accounts[sub_account.linked_account_id].append(sub_account)
    items_valuation = find_items_valuation(session, history_entry.id)
    mapped_items: Dict[Tuple[int, str], List[SubAccountItemValuationHistoryEntry]] = defaultdict(list)
    for item in items_valuation:
        mapped_items[(item.linked_account_id, item.sub_account_id)].append(item)

    return {
        "linked_accounts": [
            {
                "role": "linked_account",
                "linked_account": {
                    "id": la_v.linked_account_id,
                    "provider_id": la_v.linked_account.provider_id,
                    "description": la_v.linked_account.account_name,
                },
                "valuation": {
                    "date": (la_v.effective_snapshot.effective_at
                             if la_v.effective_snapshot
                             else history_entry.effective_at),
                    "currency": history_entry.valuation_ccy,
                    "value": la_v.valuation,
                    "change": la_v.valuation_change
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
                            "value_self_currency": sa_v.valuation_sub_account_ccy,
                            "change": sa_v.valuation_change,
                            "total_liabilities": sa_v.total_liabilities,
                            "currency": history_entry.valuation_ccy,
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
                                    "value_self_currency": item_v.valuation_sub_account_ccy,
                                    "change": item_v.valuation_change,
                                    "currency": history_entry.valuation_ccy
                                },
                                "children": [
                                    {
                                        "role": "metadata",
                                        "label": key,
                                        "value": value
                                    }
                                    for (key, value) in [
                                        ("Units", f"{item_v.units:.2f}" if item_v.units else None),
                                        (f"Value ({sa_v.sub_account_ccy})", f"{item_v.valuation_sub_account_ccy:.2f}"),
                                        ("Type", item_v.item_subtype)
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
