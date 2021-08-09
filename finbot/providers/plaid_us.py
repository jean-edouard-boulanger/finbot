from finbot import providers
from finbot.model import UserAccountPlaidSettings
from finbot.providers.errors import AuthenticationFailure
from finbot.core.serialization import serialize

from plaid import Client as PlaidClient, errors as plaid_errors

from typing import Optional, Any
from datetime import datetime


def pack_credentials(
    db_settings: dict[Any, Any], plaid_settings: UserAccountPlaidSettings
) -> dict[str, Any]:
    output: dict[str, Any] = serialize(
        {
            "access_token": str(db_settings["access_token"]),
            "item_id": str(db_settings["item_id"]),
            "plaid_settings": plaid_settings,
        }
    )
    return output


def create_plaid_client(plaid_settings: UserAccountPlaidSettings) -> PlaidClient:
    return PlaidClient(
        client_id=plaid_settings.client_id,
        secret=plaid_settings.secret_key,
        environment=plaid_settings.env,
    )


def make_account(account: dict[str, Any]) -> providers.Account:
    return {
        "id": account["name"],
        "name": account["name"],
        "iso_currency": account["balances"]["iso_currency_code"],
        "type": account["type"],
    }


class Credentials(object):
    def __init__(
        self, item_id: str, access_token: str, plaid_settings: UserAccountPlaidSettings
    ) -> None:
        self.item_id = item_id
        self.access_token = access_token
        self.plaid_settings = plaid_settings

    @property
    def user_id(self) -> str:
        return "<private>"

    @staticmethod
    def init(data: dict[Any, Any]) -> "Credentials":
        settings = data["plaid_settings"]
        return Credentials(
            item_id=data["item_id"],
            access_token=data["access_token"],
            plaid_settings=UserAccountPlaidSettings(
                user_account_id=0,
                env=settings["env"],
                client_id=settings["client_id"],
                public_key=settings["public_key"],
                secret_key=settings["secret_key"],
                created_at=datetime.now(),
                updated_at=None,
            ),
        )


class Api(providers.Base):
    def __init__(self) -> None:
        super().__init__()
        self._accounts: Optional[dict[Any, Any]] = None

    @property
    def accounts(self) -> list[dict[str, Any]]:
        assert self._accounts is not None
        accounts: list[dict[Any, Any]] = self._accounts["accounts"]
        return accounts

    def authenticate(self, credentials: Credentials) -> None:
        try:
            plaid_settings = credentials.plaid_settings
            client = create_plaid_client(plaid_settings)
            self._accounts = client.Accounts.get(credentials.access_token)
        except plaid_errors.ItemError as e:
            raise AuthenticationFailure(str(e))

    def get_balances(self) -> providers.Balances:
        return {
            "accounts": [
                {
                    "account": make_account(account),
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
                    "account": make_account(account),
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
                    "account": make_account(account),
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
