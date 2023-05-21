from dataclasses import dataclass
from typing import Literal, TypedDict

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.accounts_get_response import AccountsGetResponse
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.item_public_token_exchange_response import (
    ItemPublicTokenExchangeResponse,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_response import LinkTokenCreateResponse

from finbot import model
from finbot.core import schema as core_schema
from finbot.core.errors import FinbotError

ALL_COUNTRY_CODES = [
    CountryCode(raw_code) for raw_code in ("GB", "US", "CA", "IE", "FR", "ES", "NL")
]
FINBOT_PLAID_CLIENT_NAME = "Finbot"


class PlaidClientError(FinbotError):
    pass


class SerializedPlaidCredentials(TypedDict):
    env: str
    client_id: str
    secret_key: str


class PackedPlaidCredentials(TypedDict):
    item_id: str
    access_token: str
    plaid_credentials: SerializedPlaidCredentials


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


@dataclass(frozen=True)
class AccountData:
    name: str
    account_type: Literal["credit", "depository", "loan", "brokerage", "other"]
    balance: float
    currency: str

    @property
    def is_depository(self) -> bool:
        return self.account_type == "depository"

    @property
    def is_credit(self) -> bool:
        return self.account_type == "credit"


@dataclass(frozen=True)
class LinkToken:
    link_token: str


@dataclass(frozen=True)
class AccessToken:
    access_token: str
    item_id: str

    def dict(self) -> dict[str, str]:
        return {"access_token": self.access_token, "item_id": self.item_id}


class PlaidClient(object):
    def __init__(self, settings: PlaidSettings):
        self._settings = settings
        self._impl = plaid_api.PlaidApi(
            api_client=plaid.ApiClient(configuration=self._settings.to_plaid())
        )

    def exchange_public_token(self, public_token: str) -> AccessToken:
        try:
            response: ItemPublicTokenExchangeResponse = (
                self._impl.item_public_token_exchange(
                    item_public_token_exchange_request=ItemPublicTokenExchangeRequest(
                        public_token=public_token
                    )
                )
            )
            return AccessToken(
                access_token=response.access_token, item_id=response.item_id
            )
        except plaid.ApiException as e:
            raise PlaidClientError(
                f"failure while exchanging public Plaid token: {e}"
            ) from e

    def create_link_token(self, access_token: str) -> LinkToken:
        try:
            response: LinkTokenCreateResponse = self._impl.link_token_create(
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
            return LinkToken(link_token=response.link_token)
        except plaid.ApiException as e:
            raise PlaidClientError(
                f"failure while creating Plaid link token: {e}"
            ) from e

    def get_accounts_data(self, access_token: str) -> list[AccountData]:
        try:
            response: AccountsGetResponse = self._impl.accounts_get(
                accounts_get_request=AccountsGetRequest(access_token=access_token)
            )
            return [
                AccountData(
                    name=account_data.name,
                    account_type=account_data.type.value,
                    balance=account_data.balances.current,
                    currency=account_data.balances.iso_currency_code,
                )
                for account_data in response.accounts
            ]
        except plaid.ApiException as e:
            raise PlaidClientError(f"failure while getting Plaid accounts: {e}") from e

    @staticmethod
    def pack_credentials(
        linked_account_credentials: core_schema.CredentialsPayloadType,
        plaid_settings: PlaidSettings,
    ) -> PackedPlaidCredentials:
        return {
            "item_id": str(linked_account_credentials["item_id"]),
            "access_token": str(linked_account_credentials["access_token"]),
            "plaid_credentials": {
                "env": plaid_settings.environment,
                "client_id": plaid_settings.client_id,
                "secret_key": plaid_settings.secret_key,
            },
        }
