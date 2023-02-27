from finbot.core.qonto_api import QontoApi, SimpleAuthentication, Unauthorized
from finbot.providers.errors import AuthenticationFailure
from finbot import providers

from pydantic import BaseModel, SecretStr

from typing import Any, Optional
from copy import deepcopy


AUTH_URL = "https://app.qonto.com/signin"


class Credentials(BaseModel):
    identifier: str
    secret_key: SecretStr


class Api(providers.Base):
    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        self._accounts: Optional[providers.Balances] = None

    @staticmethod
    def description() -> str:
        return "Qonto (US)"

    @staticmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Api":
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
        self._accounts = {
            "accounts": [
                {
                    "account": {
                        "id": entry.slug,
                        "name": entry.name,
                        "iso_currency": entry.currency,
                        "type": "cash",
                    },
                    "balance": entry.balance,
                }
                for entry in organization.bank_accounts
            ]
        }

    def get_balances(self) -> providers.Balances:
        assert self._accounts
        return self._accounts

    def get_assets(self) -> providers.Assets:
        assert self._accounts is not None
        return {
            "accounts": [
                {
                    "account": deepcopy(entry["account"]),
                    "assets": [
                        {"name": "Cash", "type": "currency", "value": entry["balance"]}
                    ],
                }
                for entry in self._accounts["accounts"]
            ]
        }
