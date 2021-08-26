from finbot.apps.appwsrv.blueprints import API_V1
from finbot.apps.appwsrv.serialization import serialize_user_account
from finbot.apps.appwsrv.db import db_session
from finbot.core.web_service import Route, service_endpoint, RequestContext
from finbot.core.errors import InvalidUserInput
from finbot.core import secure, environment
from finbot.model import UserAccount

from flask import Blueprint
from flask_jwt_extended import create_access_token, create_refresh_token


AUTH: Route = API_V1.auth
auth_api = Blueprint("auth_api", __name__)


@auth_api.route(AUTH.login(), methods=["POST"])
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
    account = db_session.query(UserAccount).filter_by(email=data["email"]).first()
    not_found_message = "Invalid email or password"
    if not account:
        raise InvalidUserInput(not_found_message)

    # TODO: password should be hashed, not encrypted/decrypted with secret
    account_password = secure.fernet_decrypt(
        account.encrypted_password.encode(), environment.get_secret_key().encode()
    ).decode()
    if account_password != data["password"]:
        raise InvalidUserInput(not_found_message)

    # TODO: expires_delta should be set to a reasonable time interval
    return {
        "auth": {
            "access_token": create_access_token(
                identity=account.id, expires_delta=False
            ),
            "refresh_token": create_refresh_token(
                identity=account.id, expires_delta=False
            ),
        },
        "account": serialize_user_account(account),
    }
