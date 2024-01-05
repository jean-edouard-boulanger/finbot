from typing import Any

from finbot.core.plaid import AccountData, PlaidClient, PlaidClientError
from finbot.core.pydantic_ import SecretStr
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError
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

SchemaNamespace = "PlaidProvider"


class Credentials(BaseModel):
    item_id: str
    access_token: SecretStr


class Api(ProviderBase):
    description = "Plaid, Open Banking (US)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._accounts: list[AccountData] | None = None

    @property
    def accounts(self) -> list[AccountData]:
        assert self._accounts is not None
        return self._accounts

    def initialize(self) -> None:
        try:
            self._accounts = PlaidClient().get_accounts_data(
                access_token=self._credentials.access_token.get_secret_value()
            )
        except PlaidClientError as e:
            raise AuthenticationError(str(e))

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
                        Asset.cash(
                            currency=account.currency,
                            is_domestic=account.currency == self.user_account_currency,
                            amount=account.balance,
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
                            value_in_account_ccy=(-1.0 * account.balance),
                        )
                    ],
                )
                for account in self.accounts
                if account.is_credit
            ]
        )


def make_account(account_data: AccountData) -> Account:
    return Account(
        id=account_data.name,
        name=account_data.name,
        iso_currency=account_data.currency,
        type=account_data.account_type,
    )
