from typing import Any, Optional

from pydantic import BaseModel, SecretStr

from finbot.core.plaid import PlaidClient, PlaidClientError, PlaidSettings
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationFailure
from finbot.providers.schema import (
    Account,
    Asset,
    Assets,
    AssetsEntry,
    BalanceEntry,
    Balances,
    Liabilities,
    LiabilitiesEntry,
    Liability,
)


class PlaidCredentials(BaseModel):
    env: str
    client_id: str
    secret_key: SecretStr


class Credentials(BaseModel):
    item_id: str
    access_token: SecretStr
    plaid_credentials: PlaidCredentials


class Api(ProviderBase):
    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        self._accounts: Optional[dict[Any, Any]] = None

    @staticmethod
    def description() -> str:
        return "Plaid, Open Banking (US)"

    @staticmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

    @property
    def accounts(self) -> list[dict[str, Any]]:
        assert self._accounts is not None
        accounts: list[dict[Any, Any]] = self._accounts["accounts"]
        return accounts

    def initialize(self) -> None:
        try:
            client = self._create_plaid_client(self._credentials.plaid_credentials)
            self._accounts = client.get_accounts(
                access_token=self._credentials.access_token.get_secret_value()
            )
        except PlaidClientError as e:
            raise AuthenticationFailure(str(e))

    def get_balances(self) -> Balances:
        return Balances(
            accounts=[
                BalanceEntry(
                    account=make_account(account),
                    balance=(
                        account["balances"]["current"]
                        * (-1.0 if is_credit_account(account) else 1.0)
                    ),
                )
                for account in self.accounts
            ]
        )

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account=make_account(account),
                    assets=[
                        Asset(
                            name="Cash",
                            type="currency",
                            value=account["balances"]["current"],
                        )
                    ],
                )
                for account in self.accounts
                if is_depository_account(account)
            ]
        )

    def get_liabilities(self) -> Liabilities:
        return Liabilities(
            accounts=[
                LiabilitiesEntry(
                    account=make_account(account),
                    liabilities=[
                        Liability(
                            name="credit",
                            type="credit",
                            value=(-1.0 * account["balances"]["current"]),
                        )
                    ],
                )
                for account in self.accounts
                if is_credit_account(account)
            ]
        )

    @staticmethod
    def _create_plaid_client(credentials: PlaidCredentials) -> PlaidClient:
        return PlaidClient(
            settings=PlaidSettings(
                client_id=credentials.client_id,
                secret_key=credentials.secret_key.get_secret_value(),
                environment=credentials.env,
            )
        )


def make_account(raw_account: dict[str, Any]) -> Account:
    return Account(
        id=raw_account["name"],
        name=raw_account["name"],
        iso_currency=raw_account["balances"]["iso_currency_code"],
        type=raw_account["type"].value,
    )


def is_credit_account(account: Any) -> bool:
    return account["type"].value == "credit"


def is_depository_account(account: Any) -> bool:
    return account["type"].value == "depository"
