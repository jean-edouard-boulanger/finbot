from typing import Any

from pydantic import SecretStr

from finbot import model
from finbot.apps.appwsrv import schema
from finbot.core.email_delivery import DeliverySettings
from finbot.model import repository


def serialize_user_account(user_account: model.UserAccount) -> schema.UserAccount:
    return schema.UserAccount(
        id=user_account.id,
        email=user_account.email,
        full_name=user_account.full_name,
        mobile_phone_number=user_account.mobile_phone_number,
        created_at=user_account.created_at,
        updated_at=user_account.updated_at,
    )


def serialize_user_account_profile(
    user_account: model.UserAccount,
) -> schema.UserAccountProfile:
    return schema.UserAccountProfile(
        email=user_account.email,
        full_name=user_account.full_name,
        mobile_phone_number=user_account.mobile_phone_number,
    )


def serialize_user_account_twilio_settings(
    twilio_settings_payload: dict[str, Any] | None
) -> schema.UserAccountTwilioSettings | None:
    return (
        schema.UserAccountTwilioSettings.parse_obj(twilio_settings_payload)
        if twilio_settings_payload
        else None
    )


def serialize_user_account_plaid_settings(
    plaid_settings: model.UserAccountPlaidSettings | None,
) -> schema.UserAccountPlaidSettings | None:
    if plaid_settings is None:
        return None
    return schema.UserAccountPlaidSettings(
        env=plaid_settings.env,
        client_id=plaid_settings.client_id,
        public_key=plaid_settings.public_key,
        secret_key=SecretStr(plaid_settings.secret_key),
        created_at=plaid_settings.created_at,
        updated_at=plaid_settings.updated_at,
    )


def serialize_user_account_settings(
    settings: model.UserAccountSettings,
) -> schema.UserAccountSettings:
    return schema.UserAccountSettings(
        valuation_ccy=settings.valuation_ccy,
        twilio_settings=serialize_user_account_twilio_settings(
            settings.twilio_settings
        ),
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


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


def serialize_valuation_change(
    change: model.ValuationChangeEntry,
) -> schema.ValuationChange:
    return schema.ValuationChange(
        change_1hour=change.change_1hour,
        change_1day=change.change_1day,
        change_1week=change.change_1week,
        change_1month=change.change_1month,
        change_6months=change.change_6months,
        change_1year=change.change_1year,
        change_2years=change.change_2years,
    )


def serialize_email_delivery_settings(
    settings: DeliverySettings | None,
) -> schema.EmailDeliverySettings | None:
    return (
        schema.EmailDeliverySettings(
            subject_prefix=settings.subject_prefix,
            sender_name=settings.sender_name,
            provider_id=settings.provider_id,
            provider_settings=settings.provider_settings,
        )
        if settings
        else None
    )
