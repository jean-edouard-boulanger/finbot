import json
from dataclasses import dataclass
from typing import Self

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

from finbot.core.environment import PlaidEnvironment, get_plaid_environment
from finbot.core.errors import FinbotError
from finbot.core.schema import BaseModel, CurrencyCode

ALL_COUNTRY_CODES = [CountryCode(raw_code) for raw_code in ("GB", "US", "CA", "IE", "FR", "ES", "NL")]
FINBOT_PLAID_CLIENT_NAME = "Finbot"


class PlaidClientError(FinbotError):
    def __init__(
        self,
        error_message: str,
        error_type: str | None,
        error_code: str | None,
        request_id: str | None,
    ):
        super().__init__(error_message)
        self.error_type = error_type
        self.error_code = error_code
        self.request_id = request_id

    @classmethod
    def from_api_exception(cls, e: plaid.ApiException) -> Self:
        body = json.loads(e.body) if e.body else {}
        display_message = body.get("display_message")
        return cls(
            error_message=display_message or body.get("error_message", str(e)),
            error_type=body.get("error_type"),
            error_code=body.get("error_code"),
            request_id=body.get("request_id"),
        )


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

    @classmethod
    def from_env(cls, plaid_environment: PlaidEnvironment) -> Self:
        return cls(
            environment=plaid_environment.environment,
            client_id=plaid_environment.client_id,
            secret_key=plaid_environment.secret_key,
        )

    @classmethod
    def get_default(cls) -> Self | None:
        plaid_env = get_plaid_environment()
        return cls.from_env(plaid_env) if plaid_env else None


class AccountData(BaseModel):
    name: str
    account_type: str
    sub_type: str
    balance: float
    currency: CurrencyCode

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
    def __init__(self, settings: PlaidSettings | None = None):
        settings = settings or PlaidSettings.get_default()
        assert isinstance(settings, PlaidSettings), "missing plaid configuration"
        self._settings: PlaidSettings = settings
        self._impl = plaid_api.PlaidApi(
            api_client=plaid.ApiClient(
                configuration=self._settings.to_plaid(),
            ),
        )

    def exchange_public_token(self, public_token: str) -> AccessToken:
        try:
            response: ItemPublicTokenExchangeResponse = self._impl.item_public_token_exchange(
                item_public_token_exchange_request=ItemPublicTokenExchangeRequest(public_token=public_token)
            )
            return AccessToken(
                access_token=response.access_token,
                item_id=response.item_id,
            )
        except plaid.ApiException as e:
            raise PlaidClientError.from_api_exception(e)

    def create_link_token(self, access_token: str) -> LinkToken:
        try:
            response: LinkTokenCreateResponse = self._impl.link_token_create(
                link_token_create_request=LinkTokenCreateRequest(
                    user=LinkTokenCreateRequestUser(
                        client_user_id=self._settings.client_id,
                    ),
                    client_name=FINBOT_PLAID_CLIENT_NAME,
                    country_codes=ALL_COUNTRY_CODES,
                    language="en",
                    access_token=access_token,
                )
            )
            return LinkToken(link_token=response.link_token)
        except plaid.ApiException as e:
            raise PlaidClientError.from_api_exception(e)

    def get_accounts_data(self, access_token: str) -> list[AccountData]:
        try:
            response: AccountsGetResponse = self._impl.accounts_get(
                accounts_get_request=AccountsGetRequest(access_token=access_token)
            )
            return [
                AccountData(
                    name=account_data.name,
                    account_type=account_data.type.value,
                    sub_type=account_data.subtype.value,
                    balance=account_data.balances.current,
                    currency=account_data.balances.iso_currency_code,
                )
                for account_data in response.accounts
            ]
        except plaid.ApiException as e:
            raise PlaidClientError.from_api_exception(e)
