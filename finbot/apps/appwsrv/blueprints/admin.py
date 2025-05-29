from textwrap import dedent
from typing import Any, cast

from flask import Blueprint

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.spec import spec
from finbot.core import email_delivery
from finbot.core.email_delivery import Email, EmailService
from finbot.core.kv_store import DBKVStore
from finbot.core.spec_tree import JWT_REQUIRED, ResponseSpec
from finbot.core.web_service import get_user_account_id, jwt_required, service_endpoint
from finbot.model import repository
from finbot.model.db import db_session

admin_api = Blueprint(
    name="admin_api",
    import_name=__name__,
    url_prefix=f"{API_URL_PREFIX}/admin",
)
kv_store = DBKVStore(db_session)

ENDPOINTS_TAGS = ["Administration"]


@admin_api.route("/settings/email_delivery/providers/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetEmailDeliveryProvidersResponse,
    ),
    operation_id="get_email_delivery_providers",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_email_delivery_providers() -> appwsrv_schema.GetEmailDeliveryProvidersResponse:
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


@admin_api.route("/settings/email_delivery/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetEmailDeliverySettingsResponse,
    ),
    operation_id="get_email_delivery_settings",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_email_delivery_settings() -> appwsrv_schema.GetEmailDeliverySettingsResponse:
    """Get email delivery settings"""
    settings = kv_store.get_entity(email_delivery.DeliverySettings)
    return appwsrv_schema.GetEmailDeliverySettingsResponse(
        settings=serializer.serialize_email_delivery_settings(settings)
    )


@admin_api.route("/settings/email_delivery/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.SetEmailDeliverySettingsResponse,
    ),
    operation_id="set_email_delivery_settings",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def set_email_delivery_settings(
    json: appwsrv_schema.EmailDeliverySettings,
    query: appwsrv_schema.SetEmailDeliverySettingsParams,
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
                session=db_session,
                user_account_id=get_user_account_id(),
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
    kv_store.set_entity(delivery_settings)
    return appwsrv_schema.SetEmailDeliverySettingsResponse()


@admin_api.route("/settings/email_delivery/", methods=["DELETE"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.RemoveEmailDeliverySettingsResponse,
    ),
    operation_id="remove_email_delivery_settings",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def remove_email_delivery_settings() -> appwsrv_schema.RemoveEmailDeliverySettingsResponse:
    kv_store.delete_entity(email_delivery.DeliverySettings)
    return appwsrv_schema.RemoveEmailDeliverySettingsResponse()
