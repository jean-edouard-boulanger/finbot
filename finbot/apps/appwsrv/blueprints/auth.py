from datetime import timedelta

import bcrypt
from flask import Blueprint
from flask_jwt_extended import create_access_token, create_refresh_token

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.spec import ResponseSpec, spec
from finbot.core.errors import InvalidUserInput
from finbot.core.web_service import service_endpoint
from finbot.model import repository

auth_api = Blueprint(
    name="auth_api", import_name=__name__, url_prefix=f"{API_URL_PREFIX}/auth"
)


@auth_api.route("/login/", methods=["POST"])
@service_endpoint()
@spec.validate(resp=ResponseSpec(HTTP_200=appwsrv_schema.LoginResponse))
def auth_login(json: appwsrv_schema.LoginRequest) -> appwsrv_schema.LoginResponse:
    account = repository.find_user_account_by_email(db_session, json.email)
    not_found_message = "Invalid email or password"
    if not account:
        raise InvalidUserInput(not_found_message)

    if not bcrypt.checkpw(json.password.encode(), account.password_hash):
        raise InvalidUserInput(not_found_message)

    return appwsrv_schema.LoginResponse(
        auth=appwsrv_schema.AuthenticationPayload(
            access_token=create_access_token(
                identity=account.id, expires_delta=timedelta(days=1)
            ),
            refresh_token=create_refresh_token(
                identity=account.id, expires_delta=timedelta(days=1)
            ),
        ),
        account=serializer.serialize_user_account(account),
    )
