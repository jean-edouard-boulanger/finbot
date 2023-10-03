from typing import Any, Generator

from pydantic import BaseModel, SecretStr

from finbot.core import saxo
from finbot.core.environment import get_saxo_gateway_url
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationFailure
from finbot.providers.schema import (
    Account,
    Asset,
    Assets,
    AssetsEntry,
    BalanceEntry,
    Balances,
)


class Credentials(BaseModel):
    api_key: SecretStr


class Api(ProviderBase):
    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        saxo_gateway_url = get_saxo_gateway_url()
        assert saxo_gateway_url, "Saxo provider is not properly configured"
        self._client = saxo.SaxoGatewayClient(
            settings=saxo.SaxoGatewaySettings(gateway_url=saxo_gateway_url),
            api_key=credentials.api_key.get_secret_value(),
        )
        self._accounts: list[saxo.Account] | None = None

    @staticmethod
    def description() -> str:
        return "Saxo OpenAPI Gateway (FR)"

    @staticmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

    def initialize(self) -> None:
        try:
            self._accounts = self._client.get_accounts().Data
        except Exception as e:
            raise AuthenticationFailure(str(e))

    def iter_accounts(self) -> Generator[tuple[Account, saxo.Account], None, None]:
        assert self._accounts is not None
        for raw_account_data in self._accounts:
            yield Account(
                id=raw_account_data.AccountKey,
                name=raw_account_data.DisplayName,
                iso_currency=raw_account_data.Currency,
                type="investment",
            ), raw_account_data

    def get_balances(self) -> Balances:
        return Balances(
            accounts=[
                BalanceEntry(
                    account=account,
                    balance=self._client.get_account_balances(
                        saxo_account=saxo_account
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

    def _get_account_assets(self, saxo_account: saxo.Account) -> list[Asset]:
        assets: list[Asset] = []
        if cash_available := self._client.get_account_balances(
            saxo_account
        ).CashAvailableForTrading:
            assets.append(
                Asset(
                    name=f"Cash ({saxo_account.Currency})",
                    type="currency",
                    value=cash_available,
                )
            )
        for position in self._client.get_account_positions(saxo_account).Data:
            assets.append(_make_asset(position))
        return assets


def _make_asset(positions: saxo.NetPosition) -> Asset:
    asset_type = positions.SinglePosition.PositionBase.AssetType
    if asset_type.lower() in ("etf",):
        return Asset(
            name=positions.DisplayAndFormat.Description,
            type="equity",
            value=positions.SinglePosition.PositionView.MarketValue,
            units=positions.SinglePosition.PositionBase.Amount,
            provider_specific={
                "Symbol": positions.DisplayAndFormat.Symbol,
                "Description": positions.DisplayAndFormat.Description,
                "Equity type": positions.SinglePosition.PositionBase.AssetType,
                "Listing exchange": positions.Exchange.Description,
                "Current price": positions.SinglePosition.PositionView.CurrentPrice,
                "P&L": positions.SinglePosition.PositionView.ProfitLossOnTrade,
            },
        )
    raise ValueError(f"unknown asset type: {asset_type}")