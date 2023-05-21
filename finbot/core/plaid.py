from dataclasses import dataclass
from typing import Any, cast

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser

from finbot import model
from finbot.core.errors import FinbotError
from finbot.core.serialization import serialize

ALL_COUNTRY_CODES = [
    CountryCode(raw_code) for raw_code in ("GB", "US", "CA", "IE", "FR", "ES", "NL")
]
FINBOT_PLAID_CLIENT_NAME = "Finbot"


class PlaidClientError(FinbotError):
    pass


@dataclass(frozen=True)
class PlaidSettings:
    environment: str
    client_id: str
    secret_key: str

    def to_plaid(self) -> plaid.Configuration:
        return plaid.Configuration(
            host=getattr(plaid.Environment, self.environment.capitalize()),
            api_key={"clientId": self.client_id, "secret": self.secret_key},
        )

    @staticmethod
    def from_model(settings: model.UserAccountPlaidSettings) -> "PlaidSettings":
        return PlaidSettings(
            environment=settings.env,
            client_id=settings.client_id,
            secret_key=settings.secret_key,
        )


class PlaidClient(object):
    def __init__(self, settings: PlaidSettings):
        self._settings = settings
        self._impl = plaid_api.PlaidApi(
            api_client=plaid.ApiClient(configuration=self._settings.to_plaid())
        )

    def exchange_public_token(self, public_token: str) -> dict[str, Any]:
        try:
            response = self._impl.item_public_token_exchange(
                item_public_token_exchange_request=ItemPublicTokenExchangeRequest(
                    public_token=public_token
                )
            )
            return {
                "access_token": response["access_token"],
                "item_id": response["item_id"],
            }
        except plaid.ApiException as e:
            raise PlaidClientError(
                f"failure while exchanging public Plaid token: {e}"
            ) from e

    def create_link_token(self, access_token: str) -> str:
        try:
            response = self._impl.link_token_create(
                link_token_create_request=LinkTokenCreateRequest(
                    user=LinkTokenCreateRequestUser(
                        client_user_id=self._settings.client_id
                    ),
                    client_name=FINBOT_PLAID_CLIENT_NAME,
                    country_codes=ALL_COUNTRY_CODES,
                    language="en",
                    access_token=access_token,
                )
            )
            return cast(str, response["link_token"])
        except plaid.ApiException as e:
            raise PlaidClientError(
                f"failure while creating Plaid link token: {e}"
            ) from e

    def get_accounts(self, access_token: str) -> dict[str, Any]:
        try:
            return cast(
                dict[str, Any],
                self._impl.accounts_get(
                    accounts_get_request=AccountsGetRequest(access_token=access_token)
                ),
            )
        except plaid.ApiException as e:
            raise PlaidClientError(f"failure while getting Plaid accounts: {e}") from e

    @staticmethod
    def pack_credentials(
        linked_account_credentials: dict[Any, Any],
        plaid_settings: model.UserAccountPlaidSettings,
    ) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            serialize(
                {
                    "item_id": str(linked_account_credentials["item_id"]),
                    "access_token": str(linked_account_credentials["access_token"]),
                    "plaid_credentials": {
                        "env": plaid_settings.env,
                        "client_id": plaid_settings.client_id,
                        "secret_key": plaid_settings.secret_key,
                    },
                }
            ),
        )
