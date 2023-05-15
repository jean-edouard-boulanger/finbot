import logging

from flask import Blueprint
from sqlalchemy.exc import IntegrityError

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.core import is_active_plaid_linked_account
from finbot.apps.appwsrv.db import db_session
from finbot.core.errors import InvalidOperation, InvalidUserInput
from finbot.core.notifier import TwilioNotifier, TwilioSettings
from finbot.core.utils import unwrap_optional
from finbot.core.web_service import jwt_required, service_endpoint, validate
from finbot.model import (
    UserAccount,
    UserAccountPlaidSettings,
    UserAccountSettings,
    repository,
)

logger = logging.getLogger(__name__)

user_accounts_api = Blueprint(
    name="user_accounts_api",
    import_name=__name__,
    url_prefix=f"{API_URL_PREFIX}/accounts",
)


@user_accounts_api.route("/", methods=["POST"])
@service_endpoint()
@validate()
def create_user_account(
    body: appwsrv_schema.CreateUserAccountRequest,
) -> appwsrv_schema.CreateUserAccountResponse:
    try:
        user_account: UserAccount
        with db_session.persist(UserAccount()) as user_account:
            user_account.email = body.email
            user_account.clear_password = body.password
            user_account.full_name = body.full_name
            user_account.settings = UserAccountSettings(
                valuation_ccy=body.settings.valuation_ccy
            )
    except IntegrityError as e:
        logging.warning(f"failed to create user account: {e}")
        raise InvalidUserInput(
            f"User account with email '{user_account.email}' already exists"
        )

    return appwsrv_schema.CreateUserAccountResponse(
        user_account=serializer.serialize_user_account(user_account)
    )


@user_accounts_api.route("/<int:user_account_id>/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_user_account(user_account_id: int) -> appwsrv_schema.GetUserAccountResponse:
    user_account = repository.get_user_account(db_session, user_account_id)
    return appwsrv_schema.GetUserAccountResponse(
        user_account=serializer.serialize_user_account(user_account)
    )


@user_accounts_api.route("/<int:user_account_id>/password/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@validate()
def update_user_account_password(
    user_account_id: int, body: appwsrv_schema.UpdateUserAccountPasswordRequest
) -> appwsrv_schema.UpdateUserAccountPasswordResponse:
    account = repository.get_user_account(db_session, user_account_id)
    if body.old_password.get_secret_value() != account.clear_password:
        raise InvalidUserInput("The old password is incorrect")
    new_password = body.new_password.get_secret_value()
    if account.clear_password == new_password:
        raise InvalidUserInput(
            "The new password must be different from the old password"
        )
    with db_session.persist(account):
        account.clear_password = new_password
    return appwsrv_schema.UpdateUserAccountPasswordResponse()


@user_accounts_api.route("/<int:user_account_id>/profile/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@validate()
def update_user_account_profile(
    user_account_id: int, body: appwsrv_schema.UpdateUserAccountProfileRequest
) -> appwsrv_schema.UpdateUserAccountProfileResponse:
    user_account = repository.get_user_account(db_session, user_account_id)
    with db_session.persist(user_account):
        user_account.email = body.email
        user_account.full_name = body.full_name
        user_account.mobile_phone_number = body.mobile_phone_number
    return appwsrv_schema.UpdateUserAccountProfileResponse(
        profile=serializer.serialize_user_account_profile(user_account)
    )


@user_accounts_api.route("/<int:user_account_id>/settings/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_user_account_settings(
    user_account_id: int,
) -> appwsrv_schema.GetUserAccountSettingsResponse:
    settings = repository.get_user_account_settings(db_session, user_account_id)
    return appwsrv_schema.GetUserAccountSettingsResponse(
        settings=serializer.serialize_user_account_settings(settings)
    )


@user_accounts_api.route("/<int:user_account_id>/settings/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@validate()
def update_user_account_settings(
    user_account_id: int, body: appwsrv_schema.UpdateUserAccountSettingsRequest
) -> appwsrv_schema.UpdateUserAccountSettingsResponse:
    user_account = repository.get_user_account(db_session, user_account_id)
    settings = repository.get_user_account_settings(db_session, user_account_id)
    if not isinstance(body.twilio_settings, appwsrv_schema.UnsetField):
        serialized_twilio_settings = body.twilio_settings
        with db_session.persist(settings):
            settings.twilio_settings = (
                serialized_twilio_settings.dict()
                if serialized_twilio_settings
                else None
            )
        if serialized_twilio_settings and user_account.mobile_phone_number:
            notifier = TwilioNotifier(
                twilio_settings=TwilioSettings(
                    account_sid=serialized_twilio_settings.account_sid,
                    auth_token=serialized_twilio_settings.auth_token,
                    phone_number=serialized_twilio_settings.phone_number,
                ),
                recipient_phone_number=unwrap_optional(
                    user_account.mobile_phone_number
                ),
            )
            notifier.notify_twilio_settings_updated()
    return appwsrv_schema.UpdateUserAccountSettingsResponse(
        settings=serializer.serialize_user_account_settings(settings)
    )


@user_accounts_api.route("/<int:user_account_id>/settings/plaid/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_user_account_plaid_settings(
    user_account_id: int,
) -> appwsrv_schema.GetUserAccountPlaidSettingsResponse:
    plaid_settings = repository.get_user_account_plaid_settings(
        db_session, user_account_id
    )
    return appwsrv_schema.GetUserAccountPlaidSettingsResponse(
        plaid_settings=serializer.serialize_user_account_plaid_settings(plaid_settings)
    )


@user_accounts_api.route("/<int:user_account_id>/settings/plaid/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@validate()
def update_user_account_plaid_settings(
    user_account_id: int, body: appwsrv_schema.UpdateUserAccountPlaidSettingsRequest
) -> appwsrv_schema.UpdateUserAccountPlaidSettingsResponse:
    existing_settings = repository.get_user_account_plaid_settings(
        db_session, user_account_id
    )
    plaid_settings: UserAccountPlaidSettings
    with db_session.persist(
        existing_settings or UserAccountPlaidSettings()
    ) as plaid_settings:
        plaid_settings.user_account_id = user_account_id
        plaid_settings.env = body.env
        plaid_settings.client_id = body.client_id
        plaid_settings.public_key = body.public_key
        plaid_settings.secret_key = body.secret_key.get_secret_value()
    return appwsrv_schema.UpdateUserAccountPlaidSettingsResponse(
        plaid_settings=serializer.serialize_user_account_plaid_settings(plaid_settings)
    )


@user_accounts_api.route("/<int:user_account_id>/settings/plaid/", methods=["DELETE"])
@jwt_required()
@service_endpoint()
@validate()
def delete_user_account_plaid_settings(
    user_account_id: int,
) -> appwsrv_schema.DeleteUserAccountPlaidSettings:
    linked_accounts = repository.find_linked_accounts(db_session, user_account_id)
    for linked_account in linked_accounts:
        if is_active_plaid_linked_account(linked_account):
            raise InvalidOperation(
                "Plaid is currently in use by one or more linked accounts,"
                " please unlink or freeze these accounts first"
            )
    settings = repository.get_user_account_plaid_settings(db_session, user_account_id)
    if settings:
        db_session.delete(settings)
        db_session.commit()
    return appwsrv_schema.DeleteUserAccountPlaidSettings()


@user_accounts_api.route("/<int:user_account_id>/is_configured/")
@jwt_required()
@service_endpoint()
@validate()
def is_user_account_configured(
    user_account_id: int,
) -> appwsrv_schema.IsUserAccountConfiguredResponse:
    account = repository.get_user_account(db_session, user_account_id)
    configured = len(account.linked_accounts) > 0
    return appwsrv_schema.IsUserAccountConfiguredResponse(configured=configured)


@user_accounts_api.route("/email_available/", methods=["GET"])
@service_endpoint()
@validate()
def is_email_available(
    query: appwsrv_schema.IsEmailAvailableRequestParams,
) -> appwsrv_schema.IsEmailAvailableResponse:
    user_account = repository.find_user_account_by_email(db_session, query.email)
    return appwsrv_schema.IsEmailAvailableResponse(available=user_account is None)
