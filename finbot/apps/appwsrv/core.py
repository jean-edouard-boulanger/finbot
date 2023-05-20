import logging
from typing import Any, Optional

from plaid import Client as PlaidClient

from finbot import model
from finbot.apps.appwsrv.db import db_session
from finbot.apps.finbotwsrv.client import FinbotwsrvClient
from finbot.core import schema as core_schema
from finbot.core.errors import InvalidUserInput
from finbot.model import repository
from finbot.providers.plaid_us import pack_credentials as pack_plaid_credentials
from finbot.services.user_account_valuation import ValuationRequest
from finbot.tasks import user_account_valuation

logger = logging.getLogger(__name__)

PLAID_PROVIDER_ID = "plaid_us"


def is_plaid_linked_account(linked_account: model.LinkedAccount) -> bool:
    return linked_account.provider_id == PLAID_PROVIDER_ID


def is_active_plaid_linked_account(linked_account: model.LinkedAccount) -> bool:
    return (
        is_plaid_linked_account(linked_account)
        and not linked_account.frozen
        and not linked_account.deleted
    )


def trigger_valuation(
    user_account_id: int, linked_account_ids: list[int] | None = None
) -> None:
    logger.info(
        f"triggering valuation for account_id={user_account_id} linked_account_ids={linked_account_ids}"
    )
    account = repository.get_user_account(db_session, user_account_id)
    user_account_valuation.client.run_async(
        request=ValuationRequest(
            user_account_id=account.id, linked_accounts=linked_account_ids
        )
    )


def try_trigger_valuation(
    user_account_id: int, linked_account_ids: list[int] | None = None
) -> None:
    try:
        trigger_valuation(user_account_id, linked_account_ids)
    except Exception as e:
        logger.warning(
            f"failed to trigger valuation for account_id={user_account_id} linked_account_ids={linked_account_ids}: {e}"
        )


def validate_credentials(
    finbot_client: FinbotwsrvClient,
    plaid_settings: Optional[model.UserAccountPlaidSettings],
    provider_id: str,
    credentials: core_schema.CredentialsPayloadType,
) -> None:
    if provider_id == "plaid_us":
        assert plaid_settings is not None
        credentials = pack_plaid_credentials(credentials, plaid_settings)
    result = finbot_client.validate_credentials(
        provider_id=provider_id, credentials_data=credentials
    )
    if not result.valid:
        raise InvalidUserInput(
            f"Unable to validate provided credentials ({result.error_message})"
        )


def make_plaid_credentials(
    raw_credentials: core_schema.CredentialsPayloadType,
    plaid_settings: model.UserAccountPlaidSettings,
) -> core_schema.CredentialsPayloadType:
    plaid_client = PlaidClient(
        client_id=plaid_settings.client_id,
        secret=plaid_settings.secret_key,
        environment=plaid_settings.env,
    )
    public_token = raw_credentials["public_token"]
    response = plaid_client.Item.public_token.exchange(public_token)
    return {"access_token": response["access_token"], "item_id": response["item_id"]}


def create_plaid_link_token(
    raw_credentials: core_schema.CredentialsPayloadType,
    plaid_settings: model.UserAccountPlaidSettings,
) -> Any:
    plaid_client = PlaidClient(
        client_id=plaid_settings.client_id,
        secret=plaid_settings.secret_key,
        environment=plaid_settings.env,
    )
    link_token = plaid_client.LinkToken.create(
        {
            "user": {"client_user_id": plaid_settings.client_id},
            "client_name": "Finbot",
            "country_codes": ["GB", "US", "CA", "IE", "FR", "ES", "NL"],
            "language": "en",
            "access_token": raw_credentials["access_token"],
        }
    )["link_token"]
    return link_token


def get_plaid_access_token(
    raw_credentials: core_schema.CredentialsPayloadType,
) -> dict[str, Any]:
    return {"access_token": raw_credentials["access_token"]}
