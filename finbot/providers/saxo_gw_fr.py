from typing import Any, Generator

from pydantic.v1 import SecretStr

from finbot.core import fx_market, saxo
from finbot.core.environment import get_saxo_gateway_url
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError
from finbot.providers.schema import (
    Account,
    Asset,
    AssetClass,
    Assets,
    AssetsEntry,
    AssetType,
    BalanceEntry,
    Balances,
)

SchemaNamespace = "SaxoProvider"


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

    def initialize(self) -> None:
        try:
            self._accounts = self._client.get_accounts().Data
        except Exception as e:
            raise AuthenticationError(str(e))

    def iter_accounts(self) -> Generator[tuple[Account, saxo.SaxoAccount], None, None]:
        assert self._accounts is not None
        for raw_account_data in self._accounts:
            yield (
                Account(
                    id=raw_account_data.AccountKey,
                    name=raw_account_data.DisplayName,
                    iso_currency=CurrencyCode(raw_account_data.Currency),
                    type="investment",
                ),
                raw_account_data,
            )

    def get_balances(self) -> Balances:
        return Balances(
            accounts=[
                BalanceEntry(
                    account=account,
                    balance=self._client.get_account_balances(
                        saxo_account=saxo_account,
                    ).TotalValue,
                )
                for (account, saxo_account) in self.iter_accounts()
            ]
        )

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account=account,
                    assets=self._get_account_assets(saxo_account=saxo_account),
                )
                for (account, saxo_account) in self.iter_accounts()
            ]
        )

    def _get_account_assets(self, saxo_account: saxo.SaxoAccount) -> list[Asset]:
        assets: list[Asset] = []
        if cash_available := self._client.get_account_balances(saxo_account).CashAvailableForTrading:
            currency = CurrencyCode(saxo_account.Currency)
            assets.append(
                Asset.cash(
                    currency=currency,
                    is_domestic=currency == self.user_account_currency,
                    amount=cash_available,
                )
            )
        for position in self._client.get_account_positions(saxo_account).Data:
            assets.append(_make_asset(saxo_account, position))
        return assets


def _get_value_in_account_currency(
    saxo_account: saxo.SaxoAccount,
    position: saxo.NetPosition,
) -> float:
    value = position.SinglePosition.PositionView.MarketValue
    rate = fx_market.get_rate(
        pair=fx_market.Xccy(
            domestic=position.DisplayAndFormat.Currency,
            foreign=saxo_account.Currency,
        )
    )
    assert isinstance(rate, float)
    return rate * value


def _make_asset(
    saxo_account: saxo.SaxoAccount,
    position: saxo.NetPosition,
) -> Asset:
    asset_type = position.SinglePosition.PositionBase.AssetType
    if asset_type.lower() in ("etf", "etn", "etc"):
        return Asset(
            name=position.DisplayAndFormat.Description,
            type="equity",
            asset_class=(AssetClass.commodities if asset_type.lower() == "etc" else AssetClass.equities),
            asset_type=AssetType[asset_type.upper()],
            value=_get_value_in_account_currency(saxo_account, position),
            units=position.SinglePosition.PositionBase.Amount,
            underlying_ccy=CurrencyCode(position.DisplayAndFormat.Currency.upper()),
            provider_specific={
                "Asset currency": position.DisplayAndFormat.Currency,
                "Symbol": position.DisplayAndFormat.Symbol,
                "Description": position.DisplayAndFormat.Description,
                "Listing exchange": position.Exchange.Description,
                "Current price": position.SinglePosition.PositionView.CurrentPrice,
                "P&L": position.SinglePosition.PositionView.ProfitLossOnTrade,
            },
        )
    raise ValueError(f"unknown asset type: {asset_type}")
