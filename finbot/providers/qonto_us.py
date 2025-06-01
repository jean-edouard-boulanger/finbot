from dataclasses import dataclass
from typing import Any, Optional

from pydantic import SecretStr

from finbot.core.qonto_api import QontoApi, Unauthorized
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import some
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    Assets,
    AssetsEntry,
)

AUTH_URL = "https://app.qonto.com/signin"


class Credentials(BaseModel):
    identifier: str
    secret_key: SecretStr


@dataclass(frozen=True)
class AccountValue:
    account: Account
    account_value: float


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
        self._accounts: Optional[list[AccountValue]] = None

    def initialize(self) -> None:
        api = QontoApi(
            identifier=self._credentials.identifier,
            secret_key=self._credentials.secret_key.get_secret_value(),
        )
        try:
            organization = api.list_organizations()[0]
        except Unauthorized as e:
            raise AuthenticationError(str(e))
        self._accounts = [
            AccountValue(
                account=Account(
                    id=entry.slug,
                    name=entry.name,
                    iso_currency=CurrencyCode(entry.currency),
                    type=AccountType.depository,
                    sub_type="checking",
                ),
                account_value=entry.balance,
            )
            for entry in organization.bank_accounts
        ]

    def get_accounts(self) -> list[Account]:
        return [entry.account for entry in some(self._accounts)]

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=entry.account.id,
                    items=[
                        Asset.cash(
                            currency=entry.account.iso_currency,
                            is_domestic=entry.account.iso_currency == self.user_account_currency,
                            amount=entry.account_value,
                        )
                    ],
                )
                for entry in some(self._accounts)
            ]
        )
