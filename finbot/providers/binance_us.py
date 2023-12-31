from typing import Any, Iterator, Optional, Tuple

from binance.client import Client as Binance
from binance.exceptions import BinanceAPIException
from pydantic.v1 import SecretStr

from finbot.core.crypto_market import CryptoMarket, cryptocurrency_code
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationFailure
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

OWNERSHIP_UNITS_THRESHOLD = 0.00001
RECV_WINDOW = 60 * 1000
SchemaNamespace = "BinanceProvider"


class Credentials(BaseModel):
    api_key: SecretStr
    secret_key: SecretStr


class Api(ProviderBase):
    description = "Binance (US)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._account_ccy = "USD"
        self._crypto_market = CryptoMarket()
        self._api: Optional[Binance] = None

    def _get_account(self) -> dict[Any, Any]:
        assert self._api is not None
        account: dict[Any, Any] = self._api.get_account(recvWindow=RECV_WINDOW)
        return account

    def _account_description(self) -> Account:
        return Account(
            id="portfolio",
            name="Portfolio",
            iso_currency=CurrencyCode(self._account_ccy),
            type="investment",
        )

    def initialize(self) -> None:
        try:
            self._api = Binance(
                self._credentials.api_key.get_secret_value(),
                self._credentials.secret_key.get_secret_value(),
            )
            self._get_account()
        except BinanceAPIException as e:
            raise AuthenticationFailure(str(e))

    def _iter_holdings(self) -> Iterator[Tuple[str, float, float]]:
        for entry in self._get_account()["balances"]:
            units = float(entry["free"]) + float(entry["locked"])
            if units > OWNERSHIP_UNITS_THRESHOLD:
                symbol = entry["asset"]
                value = units * self._crypto_market.get_spot_cached(symbol, self._account_ccy)
                yield symbol, units, value

    def get_balances(self) -> Balances:
        balance = sum(value for (_, _, value) in self._iter_holdings())
        return Balances(
            accounts=[
                BalanceEntry(
                    account=self._account_description(),
                    balance=balance,
                )
            ],
        )

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account=self._account_description(),
                    assets=[
                        Asset(
                            name=symbol,
                            type="cryptocurrency",
                            asset_class=AssetClass.crypto,
                            asset_type=AssetType.crypto_currency,
                            units=units,
                            value=value,
                            underlying_ccy=cryptocurrency_code(symbol),
                        )
                        for symbol, units, value in self._iter_holdings()
                    ],
                )
            ]
        )
