from finbot.model import UserAccountPlaidSettings
from finbot.core.utils import serialize

from plaid import Client as PlaidClient

from typing import Optional
from finbot import providers

from datetime import datetime


def pack_credentials(
    db_settings: dict, plaid_settings: UserAccountPlaidSettings
) -> dict:
    return serialize(
        {
            "access_token": str(db_settings["access_token"]),
            "item_id": str(db_settings["item_id"]),
            "plaid_settings": plaid_settings,
        }
    )


def create_plaid_client(plaid_settings: UserAccountPlaidSettings):
    return PlaidClient(
        client_id=plaid_settings.client_id,
        secret=plaid_settings.secret_key,
        environment=plaid_settings.env,
    )


def make_account(account: dict):
    return {
        "id": account["name"],
        "name": account["name"],
        "iso_currency": account["balances"]["iso_currency_code"],
        "type": account["type"],
    }


class Credentials(object):
    def __init__(
        self, item_id: str, access_token: str, plaid_settings: UserAccountPlaidSettings
    ):
        self.item_id = item_id
        self.access_token = access_token
        self.plaid_settings = plaid_settings

    @property
    def user_id(self):
        return "<private>"

    @staticmethod
    def init(data):
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._accounts: Optional[dict] = None

    @property
    def accounts(self) -> dict:
        assert self._accounts is not None
        return self._accounts["accounts"]

    def authenticate(self, credentials: Credentials):
        plaid_settings = credentials.plaid_settings
        client = create_plaid_client(plaid_settings)
        self._accounts = client.Accounts.get(credentials.access_token)

    def get_balances(self) -> dict:
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

    def get_assets(self) -> dict:
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

    def get_liabilities(self) -> dict:
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
