from typing import Any, Optional

from plaid import Client as PlaidClient
from plaid import errors as plaid_errors
from pydantic import BaseModel, SecretStr

from finbot import providers
from finbot.core.serialization import serialize
from finbot.model import UserAccountPlaidSettings
from finbot.providers.errors import AuthenticationFailure


def pack_credentials(
    linked_account_credentials: dict[Any, Any], plaid_settings: UserAccountPlaidSettings
) -> dict[str, Any]:
    output: dict[str, Any] = serialize(
        {
            "item_id": str(linked_account_credentials["item_id"]),
            "access_token": str(linked_account_credentials["access_token"]),
            "plaid_credentials": {
                "env": plaid_settings.env,
                "client_id": plaid_settings.client_id,
                "public_key": plaid_settings.public_key,
                "secret_key": plaid_settings.secret_key,
            },
        }
    )
    return output


def _make_account(account: dict[str, Any]) -> providers.Account:
    return {
        "id": account["name"],
        "name": account["name"],
        "iso_currency": account["balances"]["iso_currency_code"],
        "type": account["type"],
    }


class PlaidCredentials(BaseModel):
    env: str
    client_id: str
    public_key: str
    secret_key: SecretStr


class Credentials(BaseModel):
    item_id: str
    access_token: SecretStr
    plaid_credentials: PlaidCredentials


class Api(providers.Base):
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
            self._accounts = client.Accounts.get(
                access_token=self._credentials.access_token.get_secret_value()
            )
        except plaid_errors.ItemError as e:
            raise AuthenticationFailure(str(e))

    def get_balances(self) -> providers.Balances:
        return {
            "accounts": [
                {
                    "account": _make_account(account),
                    "balance": account["balances"]["current"]
                    * (-1.0 if account["type"] == "credit" else 1.0),
                }
                for account in self.accounts
            ]
        }

    def get_assets(self) -> providers.Assets:
        return {
            "accounts": [
                {
                    "account": _make_account(account),
                    "assets": [
                        {
                            "name": "Cash",
                            "type": "currency",
                            "value": account["balances"]["current"],
                        }
                    ],
                }
                for account in self.accounts
                if account["type"] == "depository"
            ]
        }

    def get_liabilities(self) -> providers.Liabilities:
        return {
            "accounts": [
                {
                    "account": _make_account(account),
                    "liabilities": [
                        {
                            "name": "credit",
                            "type": "credit",
                            "value": -1.0 * account["balances"]["current"],
                        }
                    ],
                }
                for account in self.accounts
                if account["type"] == "credit"
            ]
        }

    @staticmethod
    def _create_plaid_client(credentials: PlaidCredentials) -> PlaidClient:
        return PlaidClient(
            client_id=credentials.client_id,
            secret=credentials.secret_key.get_secret_value(),
            environment=credentials.env,
        )
