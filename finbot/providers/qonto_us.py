from finbot.core.qonto_api import QontoApi, SimpleAuthentication, Unauthorized
from finbot.providers.errors import AuthenticationFailure
from finbot import providers

from typing import Any, Optional
from copy import deepcopy


AUTH_URL = "https://app.qonto.com/signin"


class Credentials(object):
    def __init__(self, identifier: str, secret_key: str):
        self.identifier = identifier
        self.secret_key = secret_key

    @property
    def user_id(self) -> str:
        return self.identifier

    @staticmethod
    def init(data: dict[str, Any]) -> "Credentials":
        return Credentials(data["identifier"], data["secret_key"])


class Api(providers.Base):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.accounts: Optional[providers.Balances] = None

    def authenticate(self, credentials: Credentials) -> None:
        api = QontoApi(
            SimpleAuthentication(credentials.identifier, credentials.secret_key)
        )
        try:
            organization = api.list_organizations()[0]
        except Unauthorized as e:
            raise AuthenticationFailure(str(e))
        self.accounts = {
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
        assert self.accounts
        return self.accounts

    def get_assets(self) -> providers.Assets:
        assert self.accounts is not None
        return {
            "accounts": [
                {
                    "account": deepcopy(entry["account"]),
                    "assets": [
                        {"name": "Cash", "type": "currency", "value": entry["balance"]}
                    ],
                }
                for entry in self.accounts["accounts"]
            ]
        }
