from finbot.apps.appwsrv.db import db_session
from finbot.clients import FinbotClient, WorkerClient, ValuationRequest
from finbot.core import environment
from finbot.model import repository, UserAccountPlaidSettings
from finbot.apps.finbotwsrv.errors import AuthenticationFailure
from finbot.providers.plaid_us import pack_credentials as pack_plaid_credentials

from plaid import Client as PlaidClient

from typing import Optional
import logging


def get_finbot_client() -> FinbotClient:
    return FinbotClient(environment.get_finbotwsrv_endpoint())


def get_worker_client() -> WorkerClient:
    return WorkerClient()


def trigger_valuation(
    user_account_id: int, linked_accounts: Optional[list[int]] = None
):
    account = repository.get_user_account(db_session, user_account_id)
    worker_client = get_worker_client()
    worker_client.trigger_valuation(
        ValuationRequest(user_account_id=account.id, linked_accounts=linked_accounts)
    )


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
        logging.info(finbot_response)
        user_message = finbot_response["error"]["user_message"]
        raise AuthenticationFailure(
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
