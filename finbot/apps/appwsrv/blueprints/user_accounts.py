from finbot.apps.appwsrv.blueprints import API_V1
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.serialization import (
    serialize_user_account,
    serialize_user_account_settings,
)
from finbot.apps.appwsrv import repository
from finbot.core.errors import InvalidUserInput
from finbot.core.web_service import Route, service_endpoint, RequestContext
from finbot.core.notifier import TwilioNotifier, TwilioSettings
from finbot.core.utils import unwrap_optional
from finbot.core import environment, secure
from finbot.model import (
    UserAccount,
    UserAccountSettings,
    UserAccountPlaidSettings,
)

from sqlalchemy.exc import IntegrityError

from flask import Blueprint
from flask_jwt_extended import jwt_required

import logging


logger = logging.getLogger(__name__)

ACCOUNTS: Route = API_V1.accounts
ACCOUNT: Route = ACCOUNTS.p("int:user_account_id")
user_accounts_api = Blueprint("user_accounts_api", __name__)


@user_accounts_api.route(ACCOUNTS(), methods=["POST"])
@service_endpoint(
    trace_values=False,
    schema={
        "type": "object",
        "additionalProperties": False,
        "required": ["email", "password", "full_name", "settings"],
        "properties": {
            "email": {"type": "string"},
            "password": {"type": "string"},
            "full_name": {"type": "string"},
            "settings": {
                "type": "object",
                "required": ["valuation_ccy"],
                "properties": {"valuation_ccy": {"type": "string"}},
            },
        },
    },
)
def create_user_account(request_context: RequestContext):
    data = request_context.request
    try:
        with db_session.persist(UserAccount()) as user_account:
            user_account.email = data["email"]
            user_account.encrypted_password = secure.fernet_encrypt(
                data["password"].encode(), environment.get_secret_key().encode()
            ).decode()
            user_account.full_name = data["full_name"]
            user_account.settings = UserAccountSettings(
                valuation_ccy=data["settings"]["valuation_ccy"]
            )
    except IntegrityError as e:
        logging.warning(f"failed to create user account: {e}")
        raise InvalidUserInput(
            f"User account with email '{user_account.email}' already exists"
        )

    return {"user_account": serialize_user_account(user_account)}


@user_accounts_api.route(ACCOUNT(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_user_account(user_account_id: int):
    account = repository.get_user_account(db_session, user_account_id)
    return {"user_account": serialize_user_account(account)}


@user_accounts_api.route(ACCOUNT.profile(), methods=["PUT"])
@jwt_required()
@service_endpoint(
    schema={
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "email": {"type": "string"},
            "full_name": {"type": "string"},
            "mobile_phone_number": {"type": ["string", "null"]},
        },
    }
)
def update_user_account_profile(request_context: RequestContext, user_account_id: int):
    data = request_context.request
    account = repository.get_user_account(db_session, user_account_id)
    with db_session.persist(account):
        account.email = data["email"]
        account.full_name = data["full_name"]
        account.mobile_phone_number = data["mobile_phone_number"]
    return {
        "profile": {
            "email": account.email,
            "full_name": account.full_name,
            "mobile_phone_number": account.mobile_phone_number,
        }
    }


@user_accounts_api.route(ACCOUNT.settings(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_user_account_settings(user_account_id: int):
    settings = repository.get_user_account_settings(db_session, user_account_id)
    return {"settings": serialize_user_account_settings(settings)}


@user_accounts_api.route(ACCOUNT.settings(), methods=["PUT"])
@jwt_required()
@service_endpoint(
    schema={
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "valuation_ccy": {"type": "string"},
            "twilio_settings": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "requiredProperties": ["account_sid", "auth_token", "phone_number"],
                "properties": {
                    "account_sid": {"type": "string"},
                    "auth_token": {"type": "string"},
                    "phone_number": {"type": "string"},
                },
            },
        },
    }
)
def update_user_account_settings(request_context: RequestContext, user_account_id: int):
    data = request_context.request
    user_account = repository.get_user_account(db_session, user_account_id)
    settings = repository.get_user_account_settings(db_session, user_account_id)
    if "valuation_ccy" in data:
        raise InvalidUserInput(
            "Valuation currency cannot be updated after account creation"
        )
    if "twilio_settings" in data:
        with db_session.persist(settings):
            serialized_twilio_settings = data["twilio_settings"]
            settings.twilio_settings = serialized_twilio_settings
        if serialized_twilio_settings:
            twilio_settings = TwilioSettings.deserialize(serialized_twilio_settings)
            notifier = TwilioNotifier(
                twilio_settings, unwrap_optional(user_account.mobile_phone_number)
            )
            notifier.notify_twilio_settings_updated()
    return {"settings": serialize_user_account_settings(settings)}


@user_accounts_api.route(ACCOUNT.settings.plaid(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_user_account_plaid_settings(user_account_id: int):
    settings = repository.get_user_account_plaid_settings(db_session, user_account_id)
    return {"plaid_settings": settings.serialize() if settings is not None else None}


@user_accounts_api.route(ACCOUNT.settings.plaid(), methods=["PUT"])
@jwt_required()
@service_endpoint(
    trace_values=False,
    schema={
        "type": "object",
        "additionalProperties": False,
        "required": ["env", "client_id", "public_key", "secret_key"],
        "properties": {
            "env": {"type": "string"},
            "client_id": {"type": "string"},
            "public_key": {"type": "string"},
            "secret_key": {"type": "string"},
        },
    },
)
def update_user_account_plaid_settings(
    request_context: RequestContext, user_account_id: int
):
    existing_settings = repository.get_user_account_plaid_settings(
        db_session, user_account_id
    )
    plaid_settings: UserAccountPlaidSettings
    request_data = request_context.request
    with db_session.persist(
        existing_settings or UserAccountPlaidSettings()
    ) as plaid_settings:
        plaid_settings.user_account_id = user_account_id
        plaid_settings.env = request_data["env"]
        plaid_settings.client_id = request_data["client_id"]
        plaid_settings.public_key = request_data["public_key"]
        plaid_settings.secret_key = request_data["secret_key"]
    return {"plaid_settings": plaid_settings}


@user_accounts_api.route(ACCOUNT.settings.plaid(), methods=["DELETE"])
@jwt_required()
@service_endpoint()
def delete_user_account_plaid_settings(user_account_id: int):
    settings = repository.get_user_account_plaid_settings(db_session, user_account_id)
    if settings:
        db_session.delete(settings)
        db_session.commit()
    return {}


@user_accounts_api.route(ACCOUNT.is_configured())
@jwt_required()
@service_endpoint()
def is_user_account_configured(user_account_id: int):
    account = repository.get_user_account(db_session, user_account_id)
    configured = len(account.linked_accounts) > 0
    return {"configured": configured}
