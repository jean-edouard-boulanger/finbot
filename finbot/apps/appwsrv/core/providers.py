import logging

from finbot.services.financial_data_fetcher.schema import ValidateCredentialsRequest
from finbot.services.financial_data_fetcher.workflows import ValidateCredentialsWorkflow
from finbot.core.temporal_ import get_temporal_client, temporal_workflow_id, GENERIC_TASK_QUEUE
from finbot import model
from finbot.apps.finbotwsrv.client import FinbotwsrvClient
from finbot.core import schema as core_schema
from finbot.core.environment import get_plaid_environment, is_demo, is_plaid_configured, is_saxo_configured
from finbot.core.errors import InvalidUserInput
from finbot.core.schema import CurrencyCode

logger = logging.getLogger(__name__)

PLAID_PROVIDER_ID = "plaid_us"
SAXO_PROVIDER_ID = "saxo_gw_fr"
DUMMY_PROVIDER_ID = "dummy_uk"


def is_plaid_linked_account(linked_account: model.LinkedAccount) -> bool:
    return linked_account.provider_id == PLAID_PROVIDER_ID


def is_demo_provider(provider: model.Provider) -> bool:
    if provider.id == PLAID_PROVIDER_ID:
        plaid_env = get_plaid_environment()
        if plaid_env:
            return plaid_env.is_sandbox
    if provider.id == DUMMY_PROVIDER_ID:
        return True
    return False


def is_provider_supported(provider: model.Provider) -> bool:
    if is_demo():
        return is_demo_provider(provider)

    if provider.id == PLAID_PROVIDER_ID:
        return is_plaid_configured()
    if provider.id == SAXO_PROVIDER_ID:
        return is_saxo_configured()
    return True


async def validate_credentials(
    finbot_client: FinbotwsrvClient,
    provider_id: str,
    credentials: core_schema.CredentialsPayloadType,
    user_account_currency: CurrencyCode,
) -> None:
    temporal_client = await get_temporal_client()
    result = await temporal_client.execute_workflow(
        ValidateCredentialsWorkflow,
        ValidateCredentialsRequest(
            provider_id=provider_id,
            credentials=credentials,
            user_account_currency=user_account_currency,
        ),
        id=temporal_workflow_id("app.validate_credentials."),
        task_queue=GENERIC_TASK_QUEUE,
    )
    if not result.valid:
        raise InvalidUserInput(f"Unable to validate provided credentials ({result.error_message})")
