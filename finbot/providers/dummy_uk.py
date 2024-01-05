from typing import Any

from finbot.core.schema import BaseModel, CurrencyCode
from finbot.providers.base import ProviderBase
from finbot.providers.schema import (
    Account,
    Asset,
    Assets,
    AssetsEntry,
)


class Credentials(BaseModel):
    pass


DUMMY_BALANCE: float = 1000.0
DUMMY_ACCOUNT = Account(id="dummy", name="Dummy account", iso_currency=CurrencyCode("GBP"), type="cash")
SchemaNamespace = "DummyProvider"


class Api(ProviderBase):
    description = "Dummy provider (UK)"
    credentials_type = Credentials

    def __init__(
        self,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)

    def initialize(self) -> None:
        pass

    def get_accounts(self) -> list[Account]:
        return [DUMMY_ACCOUNT]

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=DUMMY_ACCOUNT.id,
                    items=[
                        Asset.cash(
                            currency=DUMMY_ACCOUNT.iso_currency,
                            is_domestic=self.user_account_currency == DUMMY_ACCOUNT.iso_currency,
                            amount=DUMMY_BALANCE,
                        )
                    ],
                )
            ]
        )
