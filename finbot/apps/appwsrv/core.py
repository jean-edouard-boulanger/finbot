from typing import Any, Optional

from plaid import Client as PlaidClient

from finbot.apps.appwsrv.db import db_session
from finbot.apps.finbotwsrv.client import FinbotwsrvClient
from finbot.apps.workersrv import schema as workersrv_schema
from finbot.apps.workersrv.client import WorkersrvClient
from finbot.core.errors import InvalidUserInput
from finbot.core.schema import CredentialsPayloadType
from finbot.model import UserAccountPlaidSettings, repository
from finbot.providers.plaid_us import pack_credentials as pack_plaid_credentials


def trigger_valuation(
    user_account_id: int, linked_accounts: list[int] | None = None
) -> None:
    account = repository.get_user_account(db_session, user_account_id)
    worker_client = WorkersrvClient.create()
    worker_client.trigger_valuation(
        workersrv_schema.ValuationRequest(
            user_account_id=account.id, linked_accounts=linked_accounts
        )
    )


def validate_credentials(
    finbot_client: FinbotwsrvClient,
    plaid_settings: Optional[UserAccountPlaidSettings],
    provider_id: str,
    credentials: CredentialsPayloadType,
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
    raw_credentials: CredentialsPayloadType, plaid_settings: UserAccountPlaidSettings
) -> CredentialsPayloadType:
    plaid_client = PlaidClient(
        client_id=plaid_settings.client_id,
        secret=plaid_settings.secret_key,
        environment=plaid_settings.env,
    )
    public_token = raw_credentials["public_token"]
    response = plaid_client.Item.public_token.exchange(public_token)
    return {"access_token": response["access_token"], "item_id": response["item_id"]}


def create_plaid_link_token(
    raw_credentials: CredentialsPayloadType, plaid_settings: UserAccountPlaidSettings
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


def get_plaid_access_token(raw_credentials: CredentialsPayloadType) -> dict[str, Any]:
    return {"access_token": raw_credentials["access_token"]}
