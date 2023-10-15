import json
import logging
import random
import uuid

from flask import Blueprint
from sqlalchemy.exc import IntegrityError

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.core import providers as appwsrv_providers
from finbot.apps.appwsrv.core import valuation as appwsrv_valuation
from finbot.apps.appwsrv.core.formatting_rules import ACCOUNTS_PALETTE
from finbot.apps.appwsrv.db import db_session
from finbot.apps.finbotwsrv.client import FinbotwsrvClient
from finbot.core import environment, secure
from finbot.core.environment import is_plaid_configured
from finbot.core.errors import InvalidOperation, InvalidUserInput
from finbot.core.plaid import PlaidClient
from finbot.core.utils import some
from finbot.core.web_service import jwt_required, service_endpoint, validate
from finbot.model import LinkedAccount, repository
from finbot.providers.schema import CurrencyCode

logger = logging.getLogger(__name__)

linked_accounts_api = Blueprint(
    name="linked_accounts_api",
    import_name=__name__,
    url_prefix=f"{API_URL_PREFIX}/accounts/<int:user_account_id>/linked_accounts",
)


@linked_accounts_api.route("/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_linked_accounts(
    user_account_id: int,
) -> appwsrv_schema.GetLinkedAccountsResponse:
    linked_accounts = repository.find_linked_accounts(db_session, user_account_id)
    statuses = repository.get_linked_accounts_statuses(db_session, user_account_id)
    return appwsrv_schema.GetLinkedAccountsResponse(
        linked_accounts=[
            serializer.serialize_linked_account(
                linked_account=entry,
                linked_account_status=statuses.get(entry.id),
                credentials=None,
            )
            for entry in sorted(linked_accounts, key=lambda entry: entry.account_name)
        ]
    )


@linked_accounts_api.route("/", methods=["POST"])
@jwt_required()
@service_endpoint()
@validate()
def link_new_account(
    user_account_id: int,
    body: appwsrv_schema.LinkAccountRequest,
    query: appwsrv_schema.LinkAccountCommitParams,
) -> appwsrv_schema.LinkAccountResponse:
    do_validate = query.do_validate
    do_persist = query.do_persist
    logging.info(f"validate={do_validate} persist={do_persist}")

    user_account = repository.get_user_account(db_session, user_account_id)

    provider_id = body.provider_id
    provider = repository.get_provider(db_session, provider_id)

    is_plaid = provider.id == appwsrv_providers.PLAID_PROVIDER_ID
    if is_plaid and not is_plaid_configured():
        raise InvalidUserInput("user account is not setup for Plaid")
    credentials = body.credentials
    if is_plaid:
        credentials = (
            PlaidClient().exchange_public_token(credentials["public_token"]).dict()
        )

    if do_validate:
        logging.info(
            f"validating authentication details for "
            f"account_id={user_account_id} and provider_id={provider_id}"
        )
        appwsrv_providers.validate_credentials(
            finbot_client=FinbotwsrvClient.create(),
            provider_id=provider_id,
            credentials=credentials,
            user_account_currency=CurrencyCode(user_account.settings.valuation_ccy),
        )

    if do_persist:
        account_name: str = body.account_name
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
                new_linked_account.account_colour = random.choice(ACCOUNTS_PALETTE)
                new_linked_account.user_account_id = user_account.id
                new_linked_account.provider_id = body.provider_id
                new_linked_account.account_name = account_name
                new_linked_account.encrypted_credentials = secure.fernet_encrypt(
                    json.dumps(credentials).encode(),
                    environment.get_secret_key().encode(),
                ).decode()
        except IntegrityError:
            raise InvalidOperation(
                f"Provider '{provider.description}' was already linked "
                f"as '{account_name}' in this account"
            )

    if do_persist:
        appwsrv_valuation.try_trigger_valuation(
            user_account_id=user_account_id, linked_account_ids=[new_linked_account.id]
        )

    return appwsrv_schema.LinkAccountResponse()


@linked_accounts_api.route("/<int:linked_account_id>/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_linked_account(
    user_account_id: int, linked_account_id: int
) -> appwsrv_schema.GetLinkedAccountResponse:
    linked_account = repository.get_linked_account(
        db_session, user_account_id, linked_account_id
    )
    credentials = None
    if appwsrv_providers.is_plaid_linked_account(linked_account):
        credentials = json.loads(
            secure.fernet_decrypt(
                some(linked_account.encrypted_credentials).encode(),
                environment.get_secret_key().encode(),
            ).decode()
        )
        credentials = {
            "link_token": PlaidClient()
            .create_link_token(credentials["access_token"])
            .link_token
        }
    linked_account_status = repository.get_linked_account_status(
        db_session, user_account_id, linked_account_id
    )
    return appwsrv_schema.GetLinkedAccountResponse(
        linked_account=serializer.serialize_linked_account(
            linked_account=linked_account,
            linked_account_status=linked_account_status,
            credentials=credentials,
        )
    )


@linked_accounts_api.route("/<int:linked_account_id>/", methods=["DELETE"])
@jwt_required()
@service_endpoint()
@validate()
def delete_linked_account(
    user_account_id: int, linked_account_id: int
) -> appwsrv_schema.DeleteLinkedAccountResponse:
    linked_account = repository.get_linked_account(
        db_session, user_account_id, linked_account_id
    )

    with db_session.persist(linked_account):
        linked_account.account_name = (
            f"DELETED {uuid.uuid4()} / {linked_account.account_name}"
        )
        linked_account.deleted = True

    appwsrv_valuation.try_trigger_valuation(user_account_id=user_account_id)
    return appwsrv_schema.DeleteLinkedAccountResponse()


@linked_accounts_api.route("/<int:linked_account_id>/metadata/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@validate()
def update_linked_account_metadata(
    user_account_id: int,
    linked_account_id: int,
    body: appwsrv_schema.UpdateLinkedAccountMetadataRequest,
) -> appwsrv_schema.UpdateLinkedAccountMetadataResponse:
    linked_account = repository.get_linked_account(
        db_session, user_account_id, linked_account_id
    )
    if linked_account.frozen:
        raise InvalidUserInput(
            f"Linked account '{linked_account.account_name}' is frozen and cannot be updated."
        )
    with db_session.persist(linked_account):
        if account_name := body.account_name:
            if repository.linked_account_exists(
                db_session, user_account_id, account_name
            ):
                raise InvalidUserInput(
                    f"A linked account with name '{account_name}' already exists"
                )
            linked_account.account_name = account_name
        if body.frozen is True:
            linked_account.frozen = True
    return appwsrv_schema.UpdateLinkedAccountMetadataResponse()


@linked_accounts_api.route("/<int:linked_account_id>/credentials/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@validate()
def update_linked_account_credentials(
    user_account_id: int,
    linked_account_id: int,
    body: appwsrv_schema.UpdateLinkedAccountCredentialsRequest,
    query: appwsrv_schema.LinkAccountCommitParams,
) -> appwsrv_schema.UpdateLinkedAccountCredentialsResponse:
    do_validate = query.do_validate
    do_persist = query.do_persist

    linked_account_id = linked_account_id
    linked_account = repository.get_linked_account(
        db_session, user_account_id, linked_account_id
    )
    user_account_settings = repository.get_user_account_settings(
        db_session, user_account_id
    )

    if linked_account.frozen:
        raise InvalidUserInput(
            f"Linked account '{linked_account.account_name}' is frozen and cannot be updated."
        )

    is_plaid = appwsrv_providers.is_plaid_linked_account(linked_account)
    if is_plaid and not is_plaid_configured():
        raise InvalidUserInput("user account is not setup for Plaid")

    credentials = body.credentials
    if is_plaid:
        credentials = json.loads(
            secure.fernet_decrypt(
                some(linked_account.encrypted_credentials).encode(),
                environment.get_secret_key().encode(),
            ).decode()
        )

    if do_validate:
        appwsrv_providers.validate_credentials(
            finbot_client=FinbotwsrvClient.create(),
            provider_id=linked_account.provider_id,
            credentials=credentials,
            user_account_currency=CurrencyCode(user_account_settings.valuation_ccy),
        )

    if do_persist:
        with db_session.persist(linked_account):
            linked_account.encrypted_credentials = secure.fernet_encrypt(
                json.dumps(credentials).encode(), environment.get_secret_key().encode()
            ).decode()

    if do_persist:
        appwsrv_valuation.try_trigger_valuation(
            user_account_id=user_account_id, linked_account_ids=[linked_account.id]
        )

    return appwsrv_schema.UpdateLinkedAccountCredentialsResponse()
