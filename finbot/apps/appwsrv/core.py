from typing import Optional

from finbot.apps.support import ApplicationError
from finbot.clients.finbot import FinbotClient
from finbot.model import UserAccountPlaidSettings
from finbot.providers.plaid_us import pack_credentials as pack_plaid_credentials

from plaid import Client as PlaidClient


def validate_credentials(
    finbot_client: FinbotClient,
    plaid_settings: Optional[UserAccountPlaidSettings],
    provider_id: str,
    credentials: dict,
) -> None:
    if provider_id == "plaid_us":
        assert plaid_settings is not None
        credentials = pack_plaid_credentials(credentials, plaid_settings)
    finbot_response = finbot_client.get_financial_data(
        provider=provider_id, credentials_data=credentials, line_items=[]
    )
    if "error" in finbot_response:
        user_message = finbot_response["error"]["user_message"]
        raise ApplicationError(
            f"Unable to validate provided credentials ({user_message})"
        )


def make_plaid_credentials(
    raw_credentials: dict, plaid_settings: UserAccountPlaidSettings
) -> dict:
    plaid_client = PlaidClient(
        client_id=plaid_settings.client_id,
        secret=plaid_settings.secret_key,
        environment=plaid_settings.env,
    )
    public_token = raw_credentials["public_token"]
    response = plaid_client.Item.public_token.exchange(public_token)
    return {"access_token": response["access_token"], "item_id": response["item_id"]}


def create_plaid_link_token(
    raw_credentials: dict, plaid_settings: UserAccountPlaidSettings
) -> dict:
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


def get_plaid_access_token(raw_credentials: dict) -> dict:
    return {"access_token": raw_credentials["access_token"]}
