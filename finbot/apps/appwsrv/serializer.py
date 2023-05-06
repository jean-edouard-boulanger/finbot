from datetime import datetime
from typing import Any

from finbot import model
from finbot.apps.appwsrv import schema
from finbot.core import timeseries
from finbot.model import repository


def serialize_user_account(account: model.UserAccount) -> dict[str, Any]:
    return {
        "id": account.id,
        "email": account.email,
        "full_name": account.full_name,
        "mobile_phone_number": account.mobile_phone_number,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
    }


def serialize_user_account_v2(account: model.UserAccount) -> schema.UserAccount:
    return schema.UserAccount(**serialize_user_account(account))


def serialize_linked_account_status(
    linked_account_status: repository.LinkedAccountStatus | None,
) -> schema.LinkedAccountStatus | None:
    return (
        schema.LinkedAccountStatus.parse_obj(linked_account_status)
        if linked_account_status
        else None
    )


def serialize_provider(provider: model.Provider) -> schema.Provider:
    return schema.Provider(
        id=provider.id,
        description=provider.description,
        website_url=provider.website_url,
        credentials_schema=provider.credentials_schema,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


def serialize_linked_account(
    linked_account: model.LinkedAccount,
    linked_account_status: repository.LinkedAccountStatus | None,
    credentials: Any,
) -> schema.LinkedAccount:
    return schema.LinkedAccount(
        id=linked_account.id,
        user_account_id=linked_account.user_account_id,
        account_name=linked_account.account_name,
        deleted=linked_account.deleted,
        frozen=linked_account.frozen,
        provider_id=linked_account.provider.id,
        provider=serialize_provider(linked_account.provider),
        status=serialize_linked_account_status(linked_account_status),
        credentials=credentials,
        created_at=linked_account.created_at,
        updated_at=linked_account.updated_at,
    )


def serialize_user_account_valuation(
    entry: model.UserAccountHistoryEntry,
    history: list[repository.HistoricalValuationEntry],
    sparkline_schedule: list[datetime],
):
    valuation_entry = entry.user_account_valuation_history_entry
    return {
        "date": entry.effective_at,
        "currency": entry.valuation_ccy,
        "value": valuation_entry.valuation,
        "total_liabilities": valuation_entry.total_liabilities,
        "change": valuation_entry.valuation_change,
        "sparkline": [
            {
                "effective_at": valuation_time,
                "value": uas_v.last_value if uas_v is not None else None,
            }
            for valuation_time, uas_v in timeseries.schedulify(
                sparkline_schedule, history, lambda uas_v: uas_v.period_end
            )
        ],
    }


def serialize_user_account_settings(
    settings: model.UserAccountSettings,
) -> dict[str, Any]:
    return {
        "valuation_ccy": settings.valuation_ccy,
        "twilio_settings": settings.twilio_settings,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at,
    }
