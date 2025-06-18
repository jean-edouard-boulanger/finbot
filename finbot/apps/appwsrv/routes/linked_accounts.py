import logging
import uuid
from typing import Annotated

import orjson
from fastapi import APIRouter, Path, Query
from sqlalchemy.exc import IntegrityError

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.core import providers as appwsrv_providers
from finbot.apps.http_base import CurrentUserIdDep
from finbot.core import environment, secure
from finbot.core.environment import is_plaid_configured
from finbot.core.errors import InvalidOperation, InvalidUserInput, NotAllowedError
from finbot.core.jobs import JobPriority, JobSource
from finbot.core.plaid import PlaidClient
from finbot.core.schema import CurrencyCode
from finbot.core.utils import some
from finbot.model import LinkedAccount, db, persist_scope, repository
from finbot.workflows.fetch_financial_data import client as provider_client
from finbot.workflows.fetch_financial_data.schema import ValidateCredentialsRequest
from finbot.workflows.user_account_valuation import client as valuation_client
from finbot.workflows.user_account_valuation.schema import ValuationRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts/{user_account_id}/linked_accounts", tags=["Linked accounts"])


@router.get("/", operation_id="get_user_account_linked_accounts")
def get_linked_accounts(
    user_account_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.GetLinkedAccountsResponse:
    """Get linked accounts"""
    if user_account_id != current_user_id:
        raise NotAllowedError()
    linked_accounts = repository.find_linked_accounts(db.session, user_account_id)
    statuses = repository.get_linked_accounts_statuses(db.session, user_account_id)
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


@router.post("/", operation_id="link_new_account")
async def link_new_account(
    user_account_id: Annotated[int, Path()],
    json: appwsrv_schema.LinkAccountRequest,
    query: Annotated[appwsrv_schema.LinkAccountCommitParams, Query()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.LinkAccountResponse:
    """Link new account"""
    if user_account_id != current_user_id:
        raise NotAllowedError()

    do_validate = query.do_validate
    do_persist = query.do_persist
    logging.info(f"validate={do_validate} persist={do_persist}")

    user_account = repository.get_user_account(db.session, user_account_id)

    provider_id = json.provider_id
    provider = repository.get_provider(db.session, provider_id)
    if not appwsrv_providers.is_provider_supported(provider):
        raise InvalidUserInput(f"provider '{provider.id}' is not supported")

    is_plaid = provider.id == appwsrv_providers.PLAID_PROVIDER_ID
    credentials = json.credentials
    if is_plaid:
        credentials = PlaidClient().exchange_public_token(credentials["public_token"]).dict()

    if do_validate:
        logging.info(
            f"validating authentication details for account_id={user_account_id} and provider_id={provider_id}"
        )
        await provider_client.validate_credentials(
            request=ValidateCredentialsRequest(
                provider_id=provider_id,
                encrypted_credentials=secure.fernet_encrypt_json(credentials, environment.get_secret_key()).decode(),
                user_account_currency=CurrencyCode(user_account.settings.valuation_ccy),
            ),
            job_source=JobSource.app,
            priority=JobPriority.high,
        )

    if do_persist:
        account_name: str = json.account_name
        if repository.linked_account_exists(db.session, user_account_id, account_name):
            raise InvalidUserInput(f"A linked account with name '{account_name}' already exists")

        logging.info(f"Linking external account (provider_id={provider.id}) to user account_id={user_account.id}")

        try:
            new_linked_account: LinkedAccount
            with persist_scope(LinkedAccount()) as new_linked_account:
                new_linked_account.account_colour = json.account_colour
                new_linked_account.user_account_id = user_account.id
                new_linked_account.provider_id = json.provider_id
                new_linked_account.account_name = account_name
                new_linked_account.encrypted_credentials = secure.fernet_encrypt(
                    orjson.dumps(credentials),
                    environment.get_secret_key().encode(),
                ).decode()
        except IntegrityError:
            raise InvalidOperation(
                f"Provider '{provider.description}' was already linked as '{account_name}' in this account"
            )

    if do_persist:
        await valuation_client.kickoff_valuation(
            request=ValuationRequest(
                user_account_id=user_account_id,
                linked_accounts=[new_linked_account.id],
            ),
            priority=JobPriority.high,
            job_source=JobSource.app,
            ignore_errors=True,
        )

    return appwsrv_schema.LinkAccountResponse()


@router.get("/{linked_account_id}/", operation_id="get_linked_account")
def get_linked_account(
    user_account_id: Annotated[int, Path()],
    linked_account_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.GetLinkedAccountResponse:
    """Get linked account"""
    if user_account_id != current_user_id:
        raise NotAllowedError()

    linked_account = repository.get_linked_account(
        session=db.session,
        user_account_id=user_account_id,
        linked_account_id=linked_account_id,
    )
    credentials = None
    if appwsrv_providers.is_plaid_linked_account(linked_account):
        credentials = orjson.loads(
            secure.fernet_decrypt(
                some(linked_account.encrypted_credentials).encode(),
                environment.get_secret_key().encode(),
            ).decode()
        )
        credentials = {
            "link_token": PlaidClient()
            .create_link_token(
                access_token=credentials["access_token"],
            )
            .link_token,
        }
    linked_account_status = repository.get_linked_account_status(
        session=db.session,
        user_account_id=user_account_id,
        linked_account_id=linked_account_id,
    )
    return appwsrv_schema.GetLinkedAccountResponse(
        linked_account=serializer.serialize_linked_account(
            linked_account=linked_account,
            linked_account_status=linked_account_status,
            credentials=credentials,
        )
    )


@router.delete("/{linked_account_id}/", operation_id="delete_linked_account")
async def delete_linked_account(
    user_account_id: Annotated[int, Path()],
    linked_account_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.DeleteLinkedAccountResponse:
    """Delete linked account"""
    if user_account_id != current_user_id:
        raise NotAllowedError()

    linked_account = repository.get_linked_account(
        session=db.session,
        user_account_id=user_account_id,
        linked_account_id=linked_account_id,
    )

    with persist_scope(linked_account):
        linked_account.account_name = f"DELETED {uuid.uuid4()} / {linked_account.account_name}"
        linked_account.deleted = True

    await valuation_client.kickoff_valuation(
        request=ValuationRequest(
            user_account_id=user_account_id,
        ),
        priority=JobPriority.high,
        job_source=JobSource.app,
        ignore_errors=True,
    )
    return appwsrv_schema.DeleteLinkedAccountResponse()


@router.put("/{linked_account_id}/metadata/", operation_id="update_linked_account_metadata")
def update_linked_account_metadata(
    user_account_id: Annotated[int, Path()],
    linked_account_id: Annotated[int, Path()],
    json: appwsrv_schema.UpdateLinkedAccountMetadataRequest,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.UpdateLinkedAccountMetadataResponse:
    """Update linked account metadata"""
    if user_account_id != current_user_id:
        raise NotAllowedError()

    linked_account = repository.get_linked_account(
        session=db.session,
        user_account_id=user_account_id,
        linked_account_id=linked_account_id,
    )
    if linked_account.frozen:
        raise InvalidUserInput(f"Linked account '{linked_account.account_name}' is frozen and cannot be updated.")
    with persist_scope(linked_account):
        if account_name := json.account_name:
            if repository.linked_account_exists(
                session=db.session,
                user_account_id=user_account_id,
                account_name=account_name,
            ):
                raise InvalidUserInput(f"A linked account with name '{account_name}' already exists")
            linked_account.account_name = account_name
        if account_colour := json.account_colour:
            linked_account.account_colour = account_colour
        if json.frozen is True:
            linked_account.frozen = True
    return appwsrv_schema.UpdateLinkedAccountMetadataResponse()


@router.put("/{linked_account_id}/credentials/", operation_id="update_linked_account_credentials")
async def update_linked_account_credentials(
    user_account_id: Annotated[int, Path()],
    linked_account_id: Annotated[int, Path()],
    json: appwsrv_schema.UpdateLinkedAccountCredentialsRequest,
    query: Annotated[appwsrv_schema.LinkAccountCommitParams, Query()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.UpdateLinkedAccountCredentialsResponse:
    """Update linked account credentials"""
    if user_account_id != current_user_id:
        raise NotAllowedError()

    do_validate = query.do_validate
    do_persist = query.do_persist

    linked_account_id = linked_account_id
    linked_account = repository.get_linked_account(
        session=db.session,
        user_account_id=user_account_id,
        linked_account_id=linked_account_id,
    )
    user_account_settings = repository.get_user_account_settings(
        session=db.session,
        user_account_id=user_account_id,
    )

    if linked_account.frozen:
        raise InvalidUserInput(f"Linked account '{linked_account.account_name}' is frozen and cannot be updated.")

    is_plaid = appwsrv_providers.is_plaid_linked_account(linked_account)
    if is_plaid and not is_plaid_configured():
        raise InvalidUserInput("user account is not setup for Plaid")

    encrypted_credentials = (
        some(linked_account.encrypted_credentials)
        if is_plaid
        else secure.fernet_encrypt_json(json.credentials, environment.get_secret_key()).decode()
    )

    if do_validate:
        await provider_client.validate_credentials(
            request=ValidateCredentialsRequest(
                provider_id=linked_account.provider_id,
                encrypted_credentials=encrypted_credentials,
                user_account_currency=CurrencyCode(user_account_settings.valuation_ccy),
            ),
            job_source=JobSource.app,
            priority=JobPriority.high,
        )

    if do_persist:
        with persist_scope(linked_account):
            linked_account.encrypted_credentials = encrypted_credentials

    if do_persist:
        await valuation_client.kickoff_valuation(
            request=ValuationRequest(
                user_account_id=user_account_id,
                linked_accounts=[linked_account_id],
            ),
            priority=JobPriority.high,
            job_source=JobSource.app,
            ignore_errors=True,
        )

    return appwsrv_schema.UpdateLinkedAccountCredentialsResponse()
