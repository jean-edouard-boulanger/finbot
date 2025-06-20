from typing import Any, Generator

from pydantic import SecretStr

from finbot.core import saxo
from finbot.core.environment import get_saxo_gateway_url
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import some
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError, UnsupportedFinancialInstrument
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    AssetClass,
    Assets,
    AssetsEntry,
    AssetType,
)


class Credentials(BaseModel):
    api_key: SecretStr


class Api(ProviderBase):
    description = "Saxo OpenAPI Gateway (FR)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        saxo_gateway_url = get_saxo_gateway_url()
        assert saxo_gateway_url, "Saxo provider is not properly configured"
        self._client = saxo.SaxoGatewayClient(
            settings=saxo.SaxoGatewaySettings(gateway_url=saxo_gateway_url),
            api_key=credentials.api_key.get_secret_value(),
        )
        self._accounts: list[saxo.SaxoAccount] | None = None

    async def initialize(self) -> None:
        try:
            self._accounts = (await self._client.get_accounts()).Data
        except Exception as e:
            raise AuthenticationError(str(e))

    async def get_accounts(self) -> list[Account]:
        return [account for (account, _) in self._iter_accounts()]

    async def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=account.id,
                    items=(await self._get_account_assets(saxo_account=saxo_account)),
                )
                for (account, saxo_account) in self._iter_accounts()
            ]
        )

    async def _get_account_assets(self, saxo_account: saxo.SaxoAccount) -> list[Asset]:
        assets: list[Asset] = []
        if cash_available := (await self._client.get_account_balances(saxo_account)).CashAvailableForTrading:
            currency = CurrencyCode(saxo_account.Currency)
            assets.append(
                Asset.cash(
                    currency=currency,
                    is_domestic=currency == self.user_account_currency,
                    amount=cash_available,
                )
            )
        for position in (await self._client.get_account_positions(saxo_account)).Data:
            assets.append(_make_asset(position))
        return assets

    def _iter_accounts(self) -> Generator[tuple[Account, saxo.SaxoAccount], None, None]:
        for raw_account_data in some(self._accounts):
            yield (
                Account(
                    id=raw_account_data.AccountKey,
                    name=raw_account_data.DisplayName,
                    iso_currency=CurrencyCode(raw_account_data.Currency),
                    type=AccountType.investment,
                    sub_type="brokerage",
                ),
                raw_account_data,
            )


def _make_asset(
    position: saxo.NetPosition,
) -> Asset:
    asset_type = position.SinglePosition.PositionBase.AssetType
    if asset_type.lower() in ("etf", "etn", "etc"):
        return Asset(
            name=position.DisplayAndFormat.Description,
            type="equity",
            asset_class=(AssetClass.commodities if asset_type.lower() == "etc" else AssetClass.equities),
            asset_type=AssetType[asset_type.upper()],
            value_in_item_ccy=position.SinglePosition.PositionView.MarketValue,
            units=position.SinglePosition.PositionBase.Amount,
            currency=position.DisplayAndFormat.Currency,
            provider_specific={
                "Asset currency": position.DisplayAndFormat.Currency,
                "Symbol": position.DisplayAndFormat.Symbol,
                "Description": position.DisplayAndFormat.Description,
                "Listing exchange": position.Exchange.Description,
                "Current price": position.SinglePosition.PositionView.CurrentPrice,
                "P&L": position.SinglePosition.PositionView.ProfitLossOnTrade,
            },
        )
    raise UnsupportedFinancialInstrument(asset_type, position.DisplayAndFormat.Symbol)
