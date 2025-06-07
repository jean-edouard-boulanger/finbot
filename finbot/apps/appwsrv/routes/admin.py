from textwrap import dedent
from typing import Annotated, Any, cast

from fastapi import APIRouter, Query

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.http_base import CurrentUserIdDep
from finbot.core import email_delivery
from finbot.core.email_delivery import Email, EmailService
from finbot.core.kv_store import DBKVStore
from finbot.model import db, repository

router = APIRouter(
    tags=["Administration"],
)


@router.get(
    "/settings/email_delivery/providers/",
    operation_id="get_email_delivery_providers",
)
def get_email_delivery_providers(
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetEmailDeliveryProvidersResponse:
    """Get email delivery providers"""
    return appwsrv_schema.GetEmailDeliveryProvidersResponse(
        providers=[
            appwsrv_schema.EmailProviderMetadata(
                provider_id=provider_metadata["provider_id"],
                description=provider_metadata["description"],
                settings_schema=cast(dict[str, Any], provider_metadata["schema"]),
            )
            for provider_metadata in email_delivery.get_providers_metadata()
        ]
    )


@router.get(
    "/settings/email_delivery/",
    operation_id="get_email_delivery_settings",
)
def get_email_delivery_settings(
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetEmailDeliverySettingsResponse:
    """Get email delivery settings"""
    settings = DBKVStore(db.session).get_entity(email_delivery.DeliverySettings)
    return appwsrv_schema.GetEmailDeliverySettingsResponse(
        settings=serializer.serialize_email_delivery_settings(settings)
    )


@router.put(
    "/settings/email_delivery/",
    operation_id="set_email_delivery_settings",
)
def set_email_delivery_settings(
    json: appwsrv_schema.EmailDeliverySettings,
    query: Annotated[appwsrv_schema.SetEmailDeliverySettingsParams, Query()],
    user_account_id: CurrentUserIdDep,
) -> appwsrv_schema.SetEmailDeliverySettingsResponse:
    delivery_settings = email_delivery.DeliverySettings(
        subject_prefix=json.subject_prefix,
        sender_name=json.sender_name,
        provider_id=json.provider_id,
        provider_settings=json.provider_settings,
    )
    if query.do_validate:
        try:
            service = EmailService(delivery_settings)
            user_account = repository.get_user_account(
                session=db.session,
                user_account_id=user_account_id,
            )
            service.send_email(
                Email(
                    recipients_emails=[user_account.email],
                    subject="Your Finbot email delivery settings have been updated",
                    body=dedent(
                        f"""\
                    Dear {user_account.full_name},

                    Your Finbot email delivery settings have been updated.
                    """
                    ),
                )
            )
        except Exception:
            raise
    DBKVStore(db.session).set_entity(delivery_settings)
    return appwsrv_schema.SetEmailDeliverySettingsResponse()


@router.delete(
    "/settings/email_delivery/",
    operation_id="remove_email_delivery_settings",
)
def remove_email_delivery_settings(
    _: CurrentUserIdDep,
) -> appwsrv_schema.RemoveEmailDeliverySettingsResponse:
    DBKVStore(db.session).delete_entity(email_delivery.DeliverySettings)
    return appwsrv_schema.RemoveEmailDeliverySettingsResponse()
