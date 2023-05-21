import logging
from typing import Optional, cast

from finbot import model
from finbot.apps.appwsrv.db import db_session
from finbot.apps.finbotwsrv.client import FinbotwsrvClient
from finbot.core import schema as core_schema
from finbot.core.errors import InvalidUserInput
from finbot.core.plaid import PlaidClient, PlaidSettings
from finbot.model import repository
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
        credentials = cast(
            core_schema.CredentialsPayloadType,
            PlaidClient.pack_credentials(
                linked_account_credentials=credentials,
                plaid_settings=PlaidSettings.from_model(plaid_settings),
            ),
        )
    result = finbot_client.validate_credentials(
        provider_id=provider_id, credentials_data=credentials
    )
    if not result.valid:
        raise InvalidUserInput(
            f"Unable to validate provided credentials ({result.error_message})"
        )
