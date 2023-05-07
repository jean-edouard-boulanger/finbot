from textwrap import dedent

from flask import Blueprint
from flask_jwt_extended import jwt_required

from finbot.apps.appwsrv import schema, serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.db import db_session
from finbot.core import email_delivery
from finbot.core.email_delivery import Email, EmailService
from finbot.core.kv_store import DBKVStore
from finbot.core.web_service import get_user_account_id, service_endpoint, validate
from finbot.model import repository

admin_api = Blueprint(
    name="admin_api", import_name=__name__, url_prefix=f"{API_URL_PREFIX}/admin"
)
kv_store = DBKVStore(db_session)


@admin_api.route("/settings/email_delivery/providers/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_email_delivery_providers() -> schema.GetEmailDeliveryProvidersResponse:
    return schema.GetEmailDeliveryProvidersResponse(
        providers=[
            schema.EmailProviderMetadata(
                provider_id=provider_metadata["provider_id"],
                description=provider_metadata["description"],
                settings_schema=provider_metadata["schema"],
            )
            for provider_metadata in email_delivery.get_providers_metadata()
        ]
    )


@admin_api.route("/settings/email_delivery/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_email_delivery_settings() -> schema.GetEmailDeliverySettingsResponse:
    settings = kv_store.get_entity(email_delivery.DeliverySettings)
    return schema.GetEmailDeliverySettingsResponse(
        settings=serializer.serialize_email_delivery_settings(settings)
    )


@admin_api.route("/settings/email_delivery/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@validate()
def set_email_delivery_settings(
    body: schema.EmailDeliverySettings, query: schema.SetEmailDeliverySettingsParams
):
    delivery_settings = email_delivery.DeliverySettings(
        subject_prefix=body.subject_prefix,
        sender_name=body.sender_name,
        provider_id=body.provider_id,
        provider_settings=body.provider_settings,
    )
    if query.do_validate:
        try:
            service = EmailService(delivery_settings)
            user_account = repository.get_user_account(
                db_session, get_user_account_id()
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
    return {}


@admin_api.route("/settings/email_delivery/", methods=["DELETE"])
@jwt_required()
@service_endpoint()
@validate()
def remove_email_delivery_settings() -> schema.RemoveEmailDeliverySettingsResponse:
    kv_store.delete_entity(email_delivery.DeliverySettings)
    return schema.RemoveEmailDeliverySettingsResponse()
