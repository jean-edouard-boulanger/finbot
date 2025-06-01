import logging
from typing import Annotated

import bcrypt
from fastapi import APIRouter, Query
from sqlalchemy.exc import IntegrityError

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.http_base import CurrentUserIdDep
from finbot.core.errors import InvalidUserInput, NotAllowedError
from finbot.model import UserAccount, UserAccountSettings, repository
from finbot.model.db import db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["User accounts"])


@router.post(
    "/",
    operation_id="create_user_account",
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


@router.get(
    "/{user_account_id}/",
    operation_id="get_user_account",
)
def get_user_account(
    user_account_id: int,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.GetUserAccountResponse:
    if user_account_id != current_user_id:
        raise NotAllowedError()
    account = repository.get_user_account(db_session, user_account_id)
    return appwsrv_schema.GetUserAccountResponse(user_account=serializer.serialize_user_account(account))


@router.put(
    "/{user_account_id}/password/",
    operation_id="update_user_account_password",
)
def update_user_account_password(
    user_account_id: int,
    json: appwsrv_schema.UpdateUserAccountPasswordRequest,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.UpdateUserAccountPasswordResponse:
    if user_account_id != current_user_id:
        raise NotAllowedError()
    account = repository.get_user_account(db_session, user_account_id)
    old_password = json.old_password.get_secret_value()
    if not bcrypt.checkpw(old_password.encode(), account.password_hash):
        raise InvalidUserInput("The old password is incorrect")
    with db_session.persist(account):
        account.password_hash = bcrypt.hashpw(json.new_password.get_secret_value().encode(), bcrypt.gensalt())
    return appwsrv_schema.UpdateUserAccountPasswordResponse()


@router.put(
    "/{user_account_id}/profile/",
    operation_id="update_user_account_profile",
)
def update_user_account_profile(
    user_account_id: int,
    json: appwsrv_schema.UpdateUserAccountProfileRequest,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.UpdateUserAccountProfileResponse:
    if user_account_id != current_user_id:
        raise NotAllowedError()
    user_account = repository.get_user_account(db_session, user_account_id)
    with db_session.persist(user_account):
        user_account.email = json.email
        user_account.full_name = json.full_name
        user_account.mobile_phone_number = json.mobile_phone_number
    return appwsrv_schema.UpdateUserAccountProfileResponse(
        profile=serializer.serialize_user_account_profile(user_account)
    )


@router.get(
    "/{user_account_id}/settings/",
    operation_id="get_user_account_settings",
)
def get_user_account_settings(
    user_account_id: int,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.GetUserAccountSettingsResponse:
    if user_account_id != current_user_id:
        raise NotAllowedError()
    settings = repository.get_user_account_settings(db_session, user_account_id)
    return appwsrv_schema.GetUserAccountSettingsResponse(settings=serializer.serialize_user_account_settings(settings))


@router.get(
    "/{user_account_id}/is_configured/",
    operation_id="is_user_account_configured",
)
def is_user_account_configured(
    user_account_id: int,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.IsUserAccountConfiguredResponse:
    if user_account_id != current_user_id:
        raise NotAllowedError()
    account = repository.get_user_account(db_session, user_account_id)
    configured = len(account.linked_accounts) > 0
    return appwsrv_schema.IsUserAccountConfiguredResponse(configured=configured)


@router.get(
    "/email_available/",
    operation_id="is_email_available",
)
def is_email_available(
    query: Annotated[appwsrv_schema.IsEmailAvailableRequestParams, Query()],
) -> appwsrv_schema.IsEmailAvailableResponse:
    user_account = repository.find_user_account_by_email(db_session, query.email)
    return appwsrv_schema.IsEmailAvailableResponse(available=user_account is None)
