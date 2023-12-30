from typing import Any, Optional

from pydantic.v1 import SecretStr

from finbot.core.qonto_api import QontoApi, Unauthorized
from finbot.core.schema import BaseModel
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationFailure
from finbot.providers.schema import (
    Account,
    Asset,
    Assets,
    AssetsEntry,
    BalanceEntry,
    Balances,
    CurrencyCode,
)

AUTH_URL = "https://app.qonto.com/signin"
SchemaNamespace = "QontoProvider"


class Credentials(BaseModel):
    identifier: str
    secret_key: SecretStr


class Api(ProviderBase):
    description = "Qonto (US)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._accounts: Optional[Balances] = None

    def initialize(self) -> None:
        api = QontoApi(
            identifier=self._credentials.identifier,
            secret_key=self._credentials.secret_key.get_secret_value(),
        )
        try:
            organization = api.list_organizations()[0]
        except Unauthorized as e:
            raise AuthenticationFailure(str(e))
        self._accounts = Balances(
            accounts=[
                BalanceEntry(
                    account=Account(
                        id=entry.slug,
                        name=entry.name,
                        iso_currency=CurrencyCode(entry.currency),
                        type="cash",
                    ),
                    balance=entry.balance,
                )
                for entry in organization.bank_accounts
            ]
        )

    def get_balances(self) -> Balances:
        assert self._accounts
        return self._accounts

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account=entry.account,
                    assets=[
                        Asset.cash(
                            currency=entry.account.iso_currency,
                            is_domestic=entry.account.iso_currency == self.user_account_currency,
                            amount=entry.balance,
                        )
                    ],
                )
                for entry in self.get_balances().accounts
            ]
        )
