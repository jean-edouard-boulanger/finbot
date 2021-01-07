from finbot.model import UserAccountPlaidSettings
from finbot.core.utils import serialize

from plaid import Client as PlaidClient

from typing import Dict, Optional
from finbot import providers

from datetime import datetime


def pack_credentials(db_settings: Dict, plaid_settings: UserAccountPlaidSettings) -> Dict:
    return serialize({
        "access_token": str(db_settings["access_token"]),
        "item_id": str(db_settings["item_id"]),
        "plaid_settings": plaid_settings
    })


def create_plaid_client(plaid_settings: UserAccountPlaidSettings):
    return PlaidClient(
        client_id=plaid_settings.client_id,
        secret=plaid_settings.secret_key,
        environment=plaid_settings.env)


def make_account(account: Dict):
    return {
        "id": account["name"],
        "name": account["name"],
        "iso_currency": account["balances"]["iso_currency_code"],
        "type": account["type"]
    }


class Credentials(object):
    def __init__(self, item_id: str, access_token: str, plaid_settings: UserAccountPlaidSettings):
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
                updated_at=None
            )
        )


class Api(providers.Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.access_token: Optional[str] = None
        self.client: Optional[PlaidClient] = None
        self.accounts: Optional[Dict] = None

    def authenticate(self, credentials: Credentials):
        self.access_token = credentials.access_token
        plaid_settings = credentials.plaid_settings
        self.client = create_plaid_client(plaid_settings)
        self.accounts = self.client.Accounts.get(self.access_token)

    def get_balances(self) -> Dict:
        return {
            "accounts": [
                {
                    "account": make_account(account),
                    "balance": account["balances"]["current"] * (-1.0 if account["type"] == "credit" else 1.0)
                }
                for account in self.accounts["accounts"]
            ]
        }

    def get_assets(self) -> Dict:
        return {
            "accounts": [
                {
                    "account": make_account(account),
                    "assets": [{
                        "name": "Cash",
                        "type": "currency",
                        "value": account["balances"]["current"]
                    }]
                }
                for account in self.accounts["accounts"]
                if account["type"] == "depository"
            ]
        }

    def get_liabilities(self) -> Dict:
        return {
            "accounts": [
                {
                    "account": make_account(account),
                    "liabilities": [{
                        "name": "credit",
                        "type": "credit",
                        "value": -1.0 * account["balances"]["current"]
                    }]
                }
                for account in self.accounts["accounts"]
                if account["type"] == "credit"
            ]
        }
