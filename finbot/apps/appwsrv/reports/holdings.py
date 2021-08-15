from typing import Tuple
from collections import defaultdict
from datetime import timedelta

from finbot.apps.appwsrv import repository
from finbot.core import utils, timeseries
from finbot.model import (
    UserAccountHistoryEntry,
    SubAccountValuationHistoryEntry,
    SubAccountItemValuationHistoryEntry,
)


def generate(session, history_entry: UserAccountHistoryEntry):
    user_account_valuation = repository.find_user_account_valuation(
        session, history_entry.id
    )
    linked_accounts_valuation = repository.find_linked_accounts_valuation(
        session, history_entry.id
    )
    sub_accounts_valuation = repository.find_sub_accounts_valuation(
        session, history_entry.id
    )
    mapped_sub_accounts: dict[int, list[SubAccountValuationHistoryEntry]] = defaultdict(
        list
    )
    for sub_account in sub_accounts_valuation:
        mapped_sub_accounts[sub_account.linked_account_id].append(sub_account)
    items_valuation = repository.find_items_valuation(session, history_entry.id)
    mapped_items: dict[
        Tuple[int, str], list[SubAccountItemValuationHistoryEntry]
    ] = defaultdict(list)
    for item in items_valuation:
        mapped_items[(item.linked_account_id, item.sub_account_id)].append(item)

    to_time = utils.now_utc()
    from_time = to_time - timedelta(days=30)
    user_account_historical_valuation = (
        repository.find_user_account_historical_valuation(
            session=session,
            user_account_id=history_entry.user_account_id,
            from_time=from_time,
            to_time=to_time,
        )
    )
    historical_valuation_by_account = (
        repository.find_linked_accounts_historical_valuation(
            session=session,
            user_account_id=history_entry.user_account_id,
            from_time=from_time,
            to_time=to_time,
        )
    )
    sparkline_schedule = timeseries.create_schedule(
        from_time=from_time,
        to_time=to_time,
        frequency=timeseries.ScheduleFrequency.Daily,
    )

    account_valuation_history_entry = (
        user_account_valuation.account_valuation_history_entry
    )
    valuation_currency = account_valuation_history_entry.valuation_ccy

    valuation_tree = {
        "role": "user_account",
        "valuation": {
            "currency": valuation_currency,
            "value": user_account_valuation.valuation,
            "change": user_account_valuation.valuation_change,
            "sparkline": [
                uas_v.user_account_valuation_history_entry.valuation
                if uas_v is not None
                else None
                for valuation_time, uas_v in timeseries.schedulify(
                    sparkline_schedule,
                    user_account_historical_valuation,
                    lambda uas_v: uas_v.effective_at,
                )
            ],
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
                            historical_valuation_by_account.get(
                                la_v.linked_account_id, []
                            ),
                            lambda las_v: las_v.account_valuation_history_entry.effective_at,
                        )
                    ],
                },
                "children": [
                    {
                        "role": "sub_account",
                        "sub_account": {
                            "id": sa_v.sub_account_id,
                            "currency": sa_v.sub_account_ccy,
                            "description": sa_v.sub_account_description,
                            "type": sa_v.sub_account_type,
                        },
                        "valuation": {
                            "currency": valuation_currency,
                            "value": sa_v.valuation,
                            "change": sa_v.valuation_change,
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
                                    "currency": valuation_currency,
                                    "value": item_v.valuation,
                                    "change": item_v.valuation_change,
                                    "units": item_v.units,
                                },
                                "children": [
                                    {"role": "metadata", "label": key, "value": value}
                                    for (key, value) in [
                                        (
                                            "Units",
                                            f"{item_v.units:.2f}"
                                            if item_v.units
                                            else None,
                                        ),
                                        (
                                            f"Value ({sa_v.sub_account_ccy})",
                                            f"{item_v.valuation_sub_account_ccy:.2f}",
                                        ),
                                        (
                                            f"Unit value ({sa_v.sub_account_ccy})",
                                            f"{item_v.valuation_sub_account_ccy / item_v.units:.2f}"
                                            if item_v.units
                                            else None,
                                        ),
                                        ("Type", item_v.item_subtype),
                                        ("Account currency", sa_v.sub_account_ccy),
                                    ]
                                    if value is not None
                                ],
                            }
                            for item_v in mapped_items.get(
                                (sa_v.linked_account_id, sa_v.sub_account_id), []
                            )
                        ],
                    }
                    for sa_v in mapped_sub_accounts.get(la_v.linked_account_id, [])
                ],
            }
            for la_v in linked_accounts_valuation
            if not la_v.linked_account.deleted
        ],
    }

    return {"valuation_tree": valuation_tree}
