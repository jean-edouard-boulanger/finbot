from datetime import timedelta

from flask import Blueprint
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_pydantic import validate

from finbot.apps.appwsrv.schema import LoginResponse, LoginRequest, AuthenticationPayload
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.serialization import serialize_user_account_v2
from finbot.core.errors import InvalidUserInput
from finbot.core.web_service import service_endpoint
from finbot.model import repository

auth_api = Blueprint(
    name="auth_api", import_name=__name__, url_prefix=f"{API_URL_PREFIX}/auth"
)


@auth_api.route("/login/", methods=["POST"])
@service_endpoint()
@validate()
def auth_login(body: LoginRequest) -> LoginResponse:
    account = repository.find_user_account_by_email(db_session, body.email)
    not_found_message = "Invalid email or password"
    if not account:
        raise InvalidUserInput(not_found_message)

    if account.clear_password != body.password:
        raise InvalidUserInput(not_found_message)

    return LoginResponse(
        auth=AuthenticationPayload(
            access_token=create_access_token(
                identity=account.id, expires_delta=timedelta(days=1)
            ),
            refresh_token=create_refresh_token(
                identity=account.id, expires_delta=timedelta(days=1)
            )
        ),
        account=serialize_user_account_v2(account)
    )
