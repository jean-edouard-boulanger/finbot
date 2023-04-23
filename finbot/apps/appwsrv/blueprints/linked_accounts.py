import json
import logging
import uuid

from flask import Blueprint
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from finbot.apps.appwsrv import core as appwsrv_core
from finbot.apps.appwsrv.blueprints.user_accounts import ACCOUNT
from finbot.apps.appwsrv.db import db_session
from finbot.core import environment, secure
from finbot.core.errors import InvalidOperation, InvalidUserInput
from finbot.core.utils import unwrap_optional
from finbot.core.web_service import RequestContext, Route, service_endpoint
from finbot.model import LinkedAccount, repository

logger = logging.getLogger(__name__)

LINKED_ACCOUNTS: Route = ACCOUNT.linked_accounts
LINKED_ACCOUNT: Route = LINKED_ACCOUNTS.p("int:linked_account_id")
linked_accounts_api = Blueprint("linked_accounts_api", __name__)


@linked_accounts_api.route(LINKED_ACCOUNTS(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_linked_accounts(user_account_id: int):
    linked_accounts = repository.find_linked_accounts(db_session, user_account_id)
    statuses = repository.get_linked_accounts_statuses(db_session, user_account_id)
    return {
        "linked_accounts": [
            {
                "id": entry.id,
                "account_name": entry.account_name,
                "deleted": entry.deleted,
                "frozen": entry.frozen,
                "provider": entry.provider,
                "provider_id": entry.provider_id,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
                "status": statuses.get(entry.id),
            }
            for entry in sorted(linked_accounts, key=lambda entry: entry.account_name)
        ]
    }


@linked_accounts_api.route(LINKED_ACCOUNTS(), methods=["POST"])
@jwt_required()
@service_endpoint(
    trace_values=False,
    schema={
        "type": "object",
        "additionalProperties": False,
        "required": ["provider_id", "credentials", "account_name"],
        "properties": {
            "provider_id": {"type": "string"},
            "credentials": {"type": ["null", "object"]},
            "account_name": {"type": "string"},
        },
    },
    parameters={
        "validate": {"type": bool, "default": True},
        "persist": {"type": bool, "default": True},
    },
)
def link_new_account(request_context: RequestContext, user_account_id: int):
    do_validate = request_context.parameters["validate"]
    do_persist = request_context.parameters["persist"]
    request_data = request_context.request

    logging.info(f"validate={do_validate} persist={do_persist}")

    user_account = repository.get_user_account(db_session, user_account_id)

    provider_id = request_data["provider_id"]
    provider = repository.get_provider(db_session, provider_id)

    is_plaid = provider.id == "plaid_us"
    if is_plaid and not user_account.plaid_settings:
        raise InvalidUserInput("user account is not setup for Plaid")

    credentials = request_data["credentials"]
    if is_plaid:
        credentials = appwsrv_core.make_plaid_credentials(
            credentials, user_account.plaid_settings
        )

    if do_validate:
        logging.info(
            f"validating authentication details for "
            f"account_id={user_account_id} and provider_id={provider_id}"
        )
        appwsrv_core.validate_credentials(
            finbot_client=appwsrv_core.get_finbot_client(),
            plaid_settings=user_account.plaid_settings,
            provider_id=provider_id,
            credentials=credentials,
        )

    if do_persist:
        account_name: str = request_data["account_name"]
        if repository.linked_account_exists(db_session, user_account_id, account_name):
            raise InvalidUserInput(
                f"A linked account with name '{account_name}' already exists"
            )

        logging.info(
            f"Linking external account (provider_id={provider.id})"
            f" to user account_id={user_account.id}"
        )

        try:
            new_linked_account: LinkedAccount
            with db_session.persist(LinkedAccount()) as new_linked_account:
                new_linked_account.user_account_id = user_account.id
                new_linked_account.provider_id = request_data["provider_id"]
                new_linked_account.account_name = account_name
                new_linked_account.encrypted_credentials = secure.fernet_encrypt(
                    json.dumps(credentials).encode(),
                    environment.get_secret_key().encode(),
                ).decode()
        except IntegrityError:
            raise InvalidOperation(
                f"Provider '{provider.description}' was already linked "
                f"as '{request_data['account_name']}' in this account"
            )

    if do_persist:
        try:
            linked_account_id = new_linked_account.id
            logging.info(
                f"triggering partial valuation for"
                f" account_id={user_account.id}"
                f" linked_account_id={linked_account_id}"
            )
            appwsrv_core.trigger_valuation(
                user_account_id, linked_accounts=[linked_account_id]
            )
        except Exception as e:
            logging.warning(
                f"failed to trigger valuation for account_id={user_account.id}: {e}"
            )

    return {}


@linked_accounts_api.route(LINKED_ACCOUNT(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_linked_account(user_account_id: int, linked_account_id: int):
    linked_account = repository.get_linked_account(
        db_session, user_account_id, linked_account_id
    )
    credentials = None
    if linked_account.provider.id == "plaid_us":
        plaid_settings = repository.get_user_account_plaid_settings(
            db_session, user_account_id
        )
        credentials = json.loads(
            secure.fernet_decrypt(
                unwrap_optional(linked_account.encrypted_credentials).encode(),
                environment.get_secret_key().encode(),
            ).decode()
        )
        credentials["link_token"] = appwsrv_core.create_plaid_link_token(
            credentials, unwrap_optional(plaid_settings)
        )
    linked_account_status = repository.get_linked_account_status(
        db_session, user_account_id, linked_account_id
    )
    return {
        "linked_account": {
            "id": linked_account.id,
            "user_account_id": linked_account.user_account_id,
            "provider_id": linked_account.provider_id,
            "provider": linked_account.provider,
            "account_name": linked_account.account_name,
            "credentials": credentials,
            "deleted": linked_account.deleted,
            "frozen": linked_account.frozen,
            "status": linked_account_status,
            "created_at": linked_account.created_at,
            "updated_at": linked_account.updated_at,
        }
    }


@linked_accounts_api.route(LINKED_ACCOUNT.metadata(), methods=["PUT"])
@jwt_required()
@service_endpoint(
    schema={
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "account_name": {"type": ["string", "null"]},
            "frozen": {"type": ["boolean", "null"]},
        },
    }
)
def update_linked_account_metadata(
    request_context: RequestContext, user_account_id: int, linked_account_id: int
):
    request_data = request_context.request
    linked_account = repository.get_linked_account(
        db_session, user_account_id, linked_account_id
    )
    if linked_account.frozen:
        raise InvalidUserInput(
            f"Linked account '{linked_account.account_name}' is frozen and cannot be updated."
        )
    with db_session.persist(linked_account):
        if account_name := request_data.get("account_name"):
            if repository.linked_account_exists(
                db_session, user_account_id, account_name
            ):
                raise InvalidUserInput(
                    f"A linked account with name '{account_name}' already exists"
                )
            linked_account.account_name = account_name
        if request_data.get("frozen", False):
            linked_account.frozen = True
    return {}


@linked_accounts_api.route(LINKED_ACCOUNT.credentials(), methods=["PUT"])
@jwt_required()
@service_endpoint(
    trace_values=False,
    schema={
        "type": "object",
        "additionalProperties": False,
        "properties": {"credentials": {"type": ["object", "null"]}},
    },
    parameters={
        "validate": {"type": bool, "default": True},
        "persist": {"type": bool, "default": True},
    },
)
def update_linked_account_credentials(
    request_context: RequestContext, user_account_id: int, linked_account_id: int
):
    do_validate = request_context.parameters["validate"]
    do_persist = request_context.parameters["persist"]
    request_data = request_context.request

    linked_account_id = linked_account_id
    linked_account = repository.get_linked_account(
        db_session, user_account_id, linked_account_id
    )

    if linked_account.frozen:
        raise InvalidUserInput(
            f"Linked account '{linked_account.account_name}' is frozen and cannot be updated."
        )

    plaid_settings = repository.get_user_account_plaid_settings(
        db_session, user_account_id
    )

    is_plaid = linked_account.provider_id == "plaid_us"
    if is_plaid and not plaid_settings:
        raise InvalidUserInput("user account is not setup for Plaid")

    credentials = request_data["credentials"]
    if linked_account.provider.id == "plaid_us":
        credentials = json.loads(
            secure.fernet_decrypt(
                unwrap_optional(linked_account.encrypted_credentials).encode(),
                environment.get_secret_key().encode(),
            ).decode()
        )

    if do_validate:
        appwsrv_core.validate_credentials(
            finbot_client=appwsrv_core.get_finbot_client(),
            plaid_settings=plaid_settings,
            provider_id=linked_account.provider_id,
            credentials=credentials,
        )

    if do_persist:
        with db_session.persist(linked_account):
            linked_account.encrypted_credentials = secure.fernet_encrypt(
                json.dumps(credentials).encode(), environment.get_secret_key().encode()
            ).decode()

    return {}


@linked_accounts_api.route(LINKED_ACCOUNT(), methods=["DELETE"])
@jwt_required()
@service_endpoint()
def delete_linked_account(user_account_id: int, linked_account_id: int):
    linked_account = repository.get_linked_account(
        db_session, user_account_id, linked_account_id
    )

    with db_session.persist(linked_account):
        linked_account.account_name = (
            f"DELETED {uuid.uuid4()} / {linked_account.account_name}"
        )
        linked_account.deleted = True

    try:
        logging.info(f"triggering full valuation for account_id={user_account_id}")
        appwsrv_core.trigger_valuation(user_account_id)
    except Exception as e:
        logging.warning(
            f"failed to trigger valuation for account_id={user_account_id}: {e}"
        )

    return {}
