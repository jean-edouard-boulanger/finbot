from typing import Any

from finbot import model
from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.core import schema as core_schema
from finbot.core.email_delivery import DeliverySettings
from finbot.core.serialization import to_pydantic
from finbot.model import repository


def serialize_user_account(
    user_account: model.UserAccount,
) -> appwsrv_schema.UserAccount:
    return appwsrv_schema.UserAccount(
        id=user_account.id,
        email=user_account.email,
        full_name=user_account.full_name,
        mobile_phone_number=user_account.mobile_phone_number,
        created_at=user_account.created_at,
        updated_at=user_account.updated_at,
    )


def serialize_user_account_profile(
    user_account: model.UserAccount,
) -> appwsrv_schema.UserAccountProfile:
    return appwsrv_schema.UserAccountProfile(
        email=user_account.email,
        full_name=user_account.full_name,
        mobile_phone_number=user_account.mobile_phone_number,
    )


def serialize_user_account_settings(
    settings: model.UserAccountSettings,
) -> appwsrv_schema.UserAccountSettings:
    return appwsrv_schema.UserAccountSettings(
        valuation_ccy=settings.valuation_ccy,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


def serialize_linked_account_status(
    linked_account_status: repository.LinkedAccountStatus | None,
) -> appwsrv_schema.LinkedAccountStatus | None:
    return (
        appwsrv_schema.LinkedAccountStatus.parse_obj(linked_account_status)
        if linked_account_status
        else None
    )


def serialize_provider(provider: model.Provider) -> appwsrv_schema.Provider:
    return appwsrv_schema.Provider(
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
) -> appwsrv_schema.LinkedAccount:
    return appwsrv_schema.LinkedAccount(
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


def serialize_valuation_change(
    change: model.ValuationChangeEntry,
) -> core_schema.ValuationChange:
    return to_pydantic(core_schema.ValuationChange, change)


def serialize_email_delivery_settings(
    settings: DeliverySettings | None,
) -> appwsrv_schema.EmailDeliverySettings | None:
    return (
        appwsrv_schema.EmailDeliverySettings(
            subject_prefix=settings.subject_prefix,
            sender_name=settings.sender_name,
            provider_id=settings.provider_id,
            provider_settings=settings.provider_settings,
        )
        if settings
        else None
    )
