from datetime import timedelta

from flask import Blueprint
from flask_jwt_extended import create_access_token, create_refresh_token

from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.serialization import serialize_user_account
from finbot.core.errors import InvalidUserInput
from finbot.core.web_service import RequestContext, service_endpoint
from finbot.model import repository

auth_api = Blueprint(
    name="auth_api", import_name=__name__, url_prefix=f"{API_URL_PREFIX}/auth"
)


@auth_api.route("/login/", methods=["POST"])
@service_endpoint(
    trace_values=False,
    schema={
        "type": "object",
        "additionalProperties": False,
        "required": ["email", "password"],
        "properties": {"email": {"type": "string"}, "password": {"type": "string"}},
    },
)
def auth_login(request_context: RequestContext):
    data = request_context.request
    account = repository.find_user_account_by_email(db_session, data["email"])
    not_found_message = "Invalid email or password"
    if not account:
        raise InvalidUserInput(not_found_message)

    if account.clear_password != data["password"]:
        raise InvalidUserInput(not_found_message)

    return {
        "auth": {
            "access_token": create_access_token(
                identity=account.id, expires_delta=timedelta(days=1)
            ),
            "refresh_token": create_refresh_token(
                identity=account.id, expires_delta=timedelta(days=1)
            ),
        },
        "account": serialize_user_account(account),
    }
