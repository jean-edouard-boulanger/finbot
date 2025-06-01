from datetime import timedelta

import bcrypt
from fastapi import APIRouter

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.core import jwt
from finbot.core.errors import InvalidUserInput
from finbot.model import repository
from finbot.model.db import db_session

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login/",
    operation_id="authenticate_user",
)
def auth_login(json: appwsrv_schema.LoginRequest) -> appwsrv_schema.LoginResponse:
    """Authenticate user"""
    account = repository.find_user_account_by_email(db_session, json.email)
    not_found_message = "Invalid email or password"
    if not account:
        raise InvalidUserInput(not_found_message)

    if not bcrypt.checkpw(json.password.encode(), account.password_hash):
        raise InvalidUserInput(not_found_message)

    return appwsrv_schema.LoginResponse(
        auth=appwsrv_schema.AuthenticationPayload(
            access_token=jwt.create_access_token(
                identity=f"{account.id}",
                expires_delta=timedelta(days=1),
            ),
            refresh_token=jwt.create_refresh_token(
                identity=f"{account.id}",
                expires_delta=timedelta(days=1),
            ),
        ),
        account=serializer.serialize_user_account(account),
    )
