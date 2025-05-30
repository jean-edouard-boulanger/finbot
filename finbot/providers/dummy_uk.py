from typing import Any

from finbot.core.schema import BaseModel, CurrencyCode
from finbot.providers.base import ProviderBase
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    Assets,
    AssetsEntry,
)


class DummyAccountData(BaseModel):
    accounts: list[Account]
    assets: Assets


class Credentials(BaseModel):
    dummy_data: DummyAccountData | None = None


def make_dummy_account(num: int | None = None) -> Account:
    prefix = f"({num})" if num is not None else ""
    return Account(
        id=f"dummy{prefix}",
        name=f"Dummy account{prefix}",
        iso_currency=CurrencyCode("GBP"),
        type=AccountType.depository,
        sub_type="checking",
    )


DUMMY_BALANCE: float = 1000.0


def make_default_dummy_data(
    user_account_currency: CurrencyCode,
    sub_accounts_count: int = 2,
) -> DummyAccountData:
    dummy_accounts = [make_dummy_account(num if num > 0 else None) for num in range(sub_accounts_count)]
    return DummyAccountData(
        accounts=dummy_accounts,
        assets=Assets(
            accounts=[
                AssetsEntry(
                    account_id=dummy_account.id,
                    items=[
                        Asset.cash(
                            currency=dummy_account.iso_currency,
                            is_domestic=user_account_currency == dummy_account.iso_currency,
                            amount=DUMMY_BALANCE,
                        )
                    ],
                )
                for dummy_account in dummy_accounts
            ]
        ),
    )


class Api(ProviderBase):
    description = "Dummy provider (UK)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self.dummy_data = credentials.dummy_data or make_default_dummy_data(self.user_account_currency)

    def initialize(self) -> None:
        pass

    def get_accounts(self) -> list[Account]:
        return self.dummy_data.accounts

    def get_assets(self) -> Assets:
        return self.dummy_data.assets
