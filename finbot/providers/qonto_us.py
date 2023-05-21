from typing import Any, Optional

from pydantic import BaseModel, SecretStr

from finbot.core import schema as core_schema
from finbot.core.qonto_api import QontoApi, SimpleAuthentication, Unauthorized
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationFailure
from finbot.providers.schema import (
    Account,
    Asset,
    Assets,
    AssetsEntry,
    BalanceEntry,
    Balances,
)

AUTH_URL = "https://app.qonto.com/signin"


class Credentials(BaseModel):
    identifier: str
    secret_key: SecretStr


class Api(ProviderBase):
    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        self._accounts: Optional[Balances] = None

    @staticmethod
    def description() -> str:
        return "Qonto (US)"

    @staticmethod
    def create(
        authentication_payload: core_schema.CredentialsPayloadType, **kwargs: Any
    ) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

    def initialize(self) -> None:
        api = QontoApi(
            SimpleAuthentication(
                identifier=self._credentials.identifier,
                secret_key=self._credentials.secret_key.get_secret_value(),
            )
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
                        iso_currency=entry.currency,
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
                    assets=[Asset(name="Cash", type="currency", value=entry.balance)],
                )
                for entry in self.get_balances().accounts
            ]
        )
