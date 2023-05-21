from typing import Any

from pydantic import BaseModel, SecretStr

from finbot.core.plaid import AccountData, PlaidClient, PlaidClientError, PlaidSettings
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
        self._accounts: list[AccountData] | None = None

    @staticmethod
    def description() -> str:
        return "Plaid, Open Banking (US)"

    @staticmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

    @property
    def accounts(self) -> list[AccountData]:
        assert self._accounts is not None
        return self._accounts

    def initialize(self) -> None:
        try:
            client = self._create_plaid_client(self._credentials.plaid_credentials)
            self._accounts = client.get_accounts_data(
                access_token=self._credentials.access_token.get_secret_value()
            )
        except PlaidClientError as e:
            raise AuthenticationFailure(str(e))

    def get_balances(self) -> Balances:
        return Balances(
            accounts=[
                BalanceEntry(
                    account=make_account(account),
                    balance=(account.balance * (-1.0 if account.is_credit else 1.0)),
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
                            value=account.balance,
                        )
                    ],
                )
                for account in self.accounts
                if account.is_depository
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
                            value=(-1.0 * account.balance),
                        )
                    ],
                )
                for account in self.accounts
                if account.is_credit
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


def make_account(account_data: AccountData) -> Account:
    return Account(
        id=account_data.name,
        name=account_data.name,
        iso_currency=account_data.currency,
        type=account_data.account_type,
    )
