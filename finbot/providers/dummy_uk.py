from finbot import providers

from copy import deepcopy
from typing import Any


class Credentials(object):
    @property
    def user_id(self) -> str:
        return "dummy"

    @staticmethod
    def init(_: Any) -> "Credentials":
        return Credentials()


DUMMY_BALANCE: float = 1000.0
DUMMY_ACCOUNT: providers.Account = {
    "id": "dummy",
    "name": "Dummy account",
    "iso_currency": "GBP",
    "type": "cash",
}


class Api(providers.Base):
    def __init__(self) -> None:
        super().__init__()

    def authenticate(self, _: Any) -> None:
        pass

    def get_balances(self) -> providers.Balances:
        return {
            "accounts": [
                {
                    "account": deepcopy(DUMMY_ACCOUNT),
                    "balance": DUMMY_BALANCE,
                }
            ]
        }

    def get_assets(self) -> providers.Assets:
        return {
            "accounts": [
                {
                    "account": deepcopy(DUMMY_ACCOUNT),
                    "assets": [
                        {
                            "name": "Cash",
                            "type": "currency",
                            "value": DUMMY_BALANCE,
                        }
                    ],
                }
            ]
        }
