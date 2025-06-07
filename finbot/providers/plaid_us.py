from typing import Any

from pydantic import SecretStr

from finbot.core.plaid import AccountData as PlaidAccountData
from finbot.core.plaid import PlaidClient, PlaidClientError
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import some
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError, UnsupportedAccountType
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    Assets,
    AssetsEntry,
    Liabilities,
    LiabilitiesEntry,
    Liability,
)


class Credentials(BaseModel):
    item_id: str
    access_token: SecretStr


class Api(ProviderBase):
    description = "Plaid, Open Banking (US)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._plaid_accounts: list[PlaidAccountData] | None = None

    async def initialize(self) -> None:
        try:
            plaid_client = PlaidClient()
            self._plaid_accounts = await plaid_client.async_get_accounts_data(
                access_token=self._credentials.access_token.get_secret_value()
            )
        except PlaidClientError as e:
            raise AuthenticationError(str(e))
        _check_all_accounts_supported(self._plaid_accounts)

    async def get_accounts(self) -> list[Account]:
        return [_make_account(entry) for entry in some(self._plaid_accounts)]

    async def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=_make_account(plaid_account).id,
                    items=[
                        Asset.cash(
                            currency=plaid_account.currency,
                            is_domestic=plaid_account.currency == self.user_account_currency,
                            amount=plaid_account.balance,
                        )
                    ],
                )
                for plaid_account in some(self._plaid_accounts)
                if plaid_account.is_depository
            ]
        )

    async def get_liabilities(self) -> Liabilities:
        return Liabilities(
            accounts=[
                LiabilitiesEntry(
                    account_id=_make_account(account).id,
                    items=[
                        Liability(
                            name="credit",
                            type="credit",
                            value_in_item_ccy=(-1.0 * account.balance),
                            currency=account.currency,
                        )
                    ],
                )
                for account in some(self._plaid_accounts)
                if account.is_credit
            ]
        )


def _make_account(account_data: PlaidAccountData) -> Account:
    return Account(
        id=account_data.name,
        name=account_data.name,
        iso_currency=account_data.currency,
        type=AccountType[account_data.account_type],
        sub_type=account_data.sub_type,
    )


def _is_plaid_account_supported(plaid_account: PlaidAccountData) -> bool:
    return plaid_account.is_depository or plaid_account.is_credit


def _check_all_accounts_supported(plaid_accounts: list[PlaidAccountData]) -> None:
    for account in plaid_accounts:
        if not _is_plaid_account_supported(account):
            raise UnsupportedAccountType(account.account_type, account.name)
