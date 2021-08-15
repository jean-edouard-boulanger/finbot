from finbot.core import timeseries
from finbot.model import UserAccountHistoryEntry, UserAccountSettings, UserAccount

from typing import Any
from datetime import datetime


def serialize_user_account(account: UserAccount) -> dict[str, Any]:
    return {
        "id": account.id,
        "email": account.email,
        "full_name": account.full_name,
        "mobile_phone_number": account.mobile_phone_number,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }


def serialize_user_account_valuation(
    entry: UserAccountHistoryEntry,
    history: list[UserAccountHistoryEntry],
    sparkline_schedule: list[datetime],
):
    valuation_entry = entry.user_account_valuation_history_entry
    return {
        "history_entry_id": entry.id,
        "date": entry.effective_at,
        "currency": entry.valuation_ccy,
        "value": valuation_entry.valuation,
        "total_liabilities": valuation_entry.total_liabilities,
        "change": valuation_entry.valuation_change,
        "sparkline": [
            {
                "effective_at": valuation_time,
                "value": uas_v.user_account_valuation_history_entry.valuation
                if uas_v is not None
                else None,
            }
            for valuation_time, uas_v in timeseries.schedulify(
                sparkline_schedule, history, lambda uas_v: uas_v.effective_at
            )
        ],
    }


def serialize_user_account_settings(settings: UserAccountSettings) -> dict[str, Any]:
    return {
        "valuation_ccy": settings.valuation_ccy,
        "twilio_settings": settings.twilio_settings,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at,
    }
