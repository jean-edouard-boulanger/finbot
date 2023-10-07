import logging

from finbot import model
from finbot.apps.appwsrv.db import db_session
from finbot.apps.finbotwsrv.client import FinbotwsrvClient
from finbot.core import schema as core_schema
from finbot.core.environment import is_plaid_configured, is_saxo_configured
from finbot.core.errors import InvalidUserInput
from finbot.model import repository
from finbot.providers.schema import CurrencyCode
from finbot.services.user_account_valuation import ValuationRequest
from finbot.tasks import user_account_valuation

logger = logging.getLogger(__name__)

PLAID_PROVIDER_ID = "plaid_us"
SAXO_PROVIDER_ID = "saxo_gw_fr"


def is_plaid_linked_account(linked_account: model.LinkedAccount) -> bool:
    return linked_account.provider_id == PLAID_PROVIDER_ID


def is_provider_supported(provider: model.Provider) -> bool:
    if provider.id == PLAID_PROVIDER_ID:
        return is_plaid_configured()
    if provider.id == SAXO_PROVIDER_ID:
        return is_saxo_configured()
    return True


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
    provider_id: str,
    credentials: core_schema.CredentialsPayloadType,
    user_account_currency: CurrencyCode,
) -> None:
    result = finbot_client.validate_credentials(
        provider_id=provider_id,
        credentials_data=credentials,
        user_account_currency=user_account_currency,
    )
    if not result.valid:
        raise InvalidUserInput(
            f"Unable to validate provided credentials ({result.error_message})"
        )
