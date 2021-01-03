from typing import Dict, Optional
from finbot.apps.support import ApplicationError
from finbot.clients.finbot import FinbotClient
from finbot.model import UserAccountPlaidSettings, UserAccount
from finbot.providers.plaid_us import pack_credentials as pack_plaid_credentials

from plaid import Client as PlaidClient
import logging


def validate_credentials(finbot_client: FinbotClient,
                         plaid_settings: UserAccountPlaidSettings,
                         provider_id: str,
                         credentials: Optional[Dict]) -> None:
    if provider_id == "plaid_us":
        credentials = pack_plaid_credentials(
            credentials, plaid_settings)
        logging.info(credentials)
    finbot_response = finbot_client.get_financial_data(
        provider=provider_id,
        credentials_data=credentials,
        line_items=[])

    if "error" in finbot_response:
        user_message = finbot_response["error"]["user_message"]
        raise ApplicationError(f"Unable to validate provided credentials ({user_message})")


def make_plaid_credentials(raw_credentials: Dict, plaid_settings: UserAccountPlaidSettings):
    plaid_client = PlaidClient(
        client_id=plaid_settings.client_id,
        secret=plaid_settings.secret_key,
        environment=plaid_settings.env)
    public_token = raw_credentials["public_token"]
    response = plaid_client.Item.public_token.exchange(public_token)
    return {
        "access_token": response["access_token"],
        "item_id": response["item_id"]
    }
