from finbot import providers

from pydantic import BaseModel

from copy import deepcopy
from typing import Any


class Credentials(BaseModel):
    pass


DUMMY_BALANCE: float = 1000.0
DUMMY_ACCOUNT: providers.Account = {
    "id": "dummy",
    "name": "Dummy account",
    "iso_currency": "GBP",
    "type": "cash",
}


class Api(providers.Base):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @staticmethod
    def description() -> str:
        return "Dummy provider (UK)"

    @staticmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Api":
        return Api(**kwargs)

    def initialize(self) -> None:
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
