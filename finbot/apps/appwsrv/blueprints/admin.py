from finbot.apps.appwsrv.blueprints import API_V1
from finbot.apps.appwsrv.db import db_session
from finbot.core.email_delivery import EmailService, Email
from finbot.core import email_delivery
from finbot.core.web_service import Route, service_endpoint, RequestContext
from finbot.core.kv_store import DBKVStore
from finbot.model import repository

from flask import Blueprint
from flask_jwt_extended import jwt_required

from textwrap import dedent

ADMIN: Route = API_V1.admin
admin_api = Blueprint("admin_api", __name__)
kv_store = DBKVStore(db_session)


@admin_api.route(ADMIN.settings.email_delivery.providers(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_email_delivery_providers():
    return {
        "providers": email_delivery.get_providers_metadata(),
    }


@admin_api.route(ADMIN.settings.email_delivery(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_email_delivery_settings():
    email_settings = kv_store.get_entity(email_delivery.DeliverySettings)
    return {
        "settings": email_settings,
    }


@admin_api.route(ADMIN.settings.email_delivery(), methods=["PUT"])
@jwt_required()
@service_endpoint(parameters={"validate": {"type": bool, "default": False}})
def set_email_delivery_settings(request_context: RequestContext):
    validate = request_context.parameters["validate"]
    delivery_settings = email_delivery.DeliverySettings.deserialize(
        request_context.request
    )
    if validate:
        try:
            service = EmailService(delivery_settings)
            user_account = repository.get_user_account(
                db_session, request_context.user_id
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


@admin_api.route(ADMIN.settings.email_delivery(), methods=["DELETE"])
@jwt_required()
@service_endpoint()
def remove_email_delivery_settings():
    kv_store.delete_entity(email_delivery.DeliverySettings)
    return {}
