from typing import Any

from pydantic import BaseModel

from finbot.providers.base import ProviderBase
from finbot.providers.schema import (
    Account,
    Asset,
    Assets,
    AssetsEntry,
    BalanceEntry,
    Balances,
)


class Credentials(BaseModel):
    pass


DUMMY_BALANCE: float = 1000.0
DUMMY_ACCOUNT = Account(
    id="dummy", name="Dummy account", iso_currency="GBP", type="cash"
)


class Api(ProviderBase):
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

    def get_balances(self) -> Balances:
        return Balances(
            accounts=[BalanceEntry(account=DUMMY_ACCOUNT, balance=DUMMY_BALANCE)]
        )

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account=DUMMY_ACCOUNT,
                    assets=[Asset(name="Cash", type="currency", value=DUMMY_BALANCE)],
                )
            ]
        )
