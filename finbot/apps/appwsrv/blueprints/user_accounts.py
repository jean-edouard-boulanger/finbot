import logging

import bcrypt
from flask import Blueprint
from sqlalchemy.exc import IntegrityError

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.spec import spec
from finbot.core.errors import InvalidUserInput
from finbot.core.spec_tree import JWT_REQUIRED, ResponseSpec
from finbot.core.web_service import jwt_required, service_endpoint
from finbot.model import UserAccount, UserAccountSettings, repository
from finbot.model.db import db_session

logger = logging.getLogger(__name__)

user_accounts_api = Blueprint(
    name="user_accounts_api",
    import_name=__name__,
    url_prefix=f"{API_URL_PREFIX}/accounts",
)


ENDPOINTS_TAGS = ["User accounts"]


@user_accounts_api.route("/", methods=["POST"])
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.CreateUserAccountResponse,
    ),
    operation_id="create_user_account",
    tags=ENDPOINTS_TAGS,
)
def create_user_account(
    json: appwsrv_schema.CreateUserAccountRequest,
) -> appwsrv_schema.CreateUserAccountResponse:
    try:
        user_account: UserAccount
        with db_session.persist(UserAccount()) as user_account:
            user_account.email = json.email
            user_account.password_hash = bcrypt.hashpw(json.password.get_secret_value().encode(), bcrypt.gensalt())
            user_account.full_name = json.full_name
            user_account.settings = UserAccountSettings(valuation_ccy=json.settings.valuation_ccy)
    except IntegrityError as e:
        logging.warning(f"failed to create user account: {e}")
        raise InvalidUserInput(f"User account with email '{user_account.email}' already exists")

    return appwsrv_schema.CreateUserAccountResponse(user_account=serializer.serialize_user_account(user_account))


@user_accounts_api.route("/<int:user_account_id>/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetUserAccountResponse,
    ),
    operation_id="get_user_account",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_user_account(
    user_account_id: int,
) -> appwsrv_schema.GetUserAccountResponse:
    user_account = repository.get_user_account(db_session, user_account_id)
    return appwsrv_schema.GetUserAccountResponse(user_account=serializer.serialize_user_account(user_account))


@user_accounts_api.route("/<int:user_account_id>/password/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.UpdateUserAccountPasswordResponse,
    ),
    operation_id="update_user_account_password",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def update_user_account_password(
    user_account_id: int,
    json: appwsrv_schema.UpdateUserAccountPasswordRequest,
) -> appwsrv_schema.UpdateUserAccountPasswordResponse:
    account = repository.get_user_account(db_session, user_account_id)
    old_password = json.old_password.get_secret_value()
    if not bcrypt.checkpw(old_password.encode(), account.password_hash):
        raise InvalidUserInput("The old password is incorrect")
    with db_session.persist(account):
        account.password_hash = bcrypt.hashpw(json.new_password.get_secret_value().encode(), bcrypt.gensalt())
    return appwsrv_schema.UpdateUserAccountPasswordResponse()


@user_accounts_api.route("/<int:user_account_id>/profile/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.UpdateUserAccountProfileResponse,
    ),
    operation_id="update_user_account_profile",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def update_user_account_profile(
    user_account_id: int,
    json: appwsrv_schema.UpdateUserAccountProfileRequest,
) -> appwsrv_schema.UpdateUserAccountProfileResponse:
    user_account = repository.get_user_account(db_session, user_account_id)
    with db_session.persist(user_account):
        user_account.email = json.email
        user_account.full_name = json.full_name
        user_account.mobile_phone_number = json.mobile_phone_number
    return appwsrv_schema.UpdateUserAccountProfileResponse(
        profile=serializer.serialize_user_account_profile(user_account)
    )


@user_accounts_api.route("/<int:user_account_id>/settings/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetUserAccountSettingsResponse,
    ),
    operation_id="get_user_account_settings",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_user_account_settings(
    user_account_id: int,
) -> appwsrv_schema.GetUserAccountSettingsResponse:
    settings = repository.get_user_account_settings(db_session, user_account_id)
    return appwsrv_schema.GetUserAccountSettingsResponse(settings=serializer.serialize_user_account_settings(settings))


@user_accounts_api.route("/<int:user_account_id>/is_configured/")
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.IsUserAccountConfiguredResponse,
    ),
    operation_id="is_user_account_configured",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def is_user_account_configured(
    user_account_id: int,
) -> appwsrv_schema.IsUserAccountConfiguredResponse:
    account = repository.get_user_account(db_session, user_account_id)
    configured = len(account.linked_accounts) > 0
    return appwsrv_schema.IsUserAccountConfiguredResponse(configured=configured)


@user_accounts_api.route("/email_available/", methods=["GET"])
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.IsEmailAvailableResponse,
    ),
    operation_id="is_email_available",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def is_email_available(
    query: appwsrv_schema.IsEmailAvailableRequestParams,
) -> appwsrv_schema.IsEmailAvailableResponse:
    user_account = repository.find_user_account_by_email(db_session, query.email)
    return appwsrv_schema.IsEmailAvailableResponse(available=user_account is None)
