from typing import Any, Iterator, Optional, Tuple

import krakenex
from pydantic.v1 import SecretStr

from finbot.core import fx_market
from finbot.core.errors import FinbotError
from finbot.core.schema import BaseModel
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
    CurrencyCode,
)

OWNERSHIP_UNITS_THRESHOLD = 0.00001
SchemaNamespace = "KrakenProvider"


class Credentials(BaseModel):
    api_key: SecretStr
    private_key: SecretStr


def _format_error(errors: list[str]) -> str:
    return ", ".join(errors)


def _is_cash(symbol: str) -> bool:
    return symbol.startswith("Z")


def _demangle_symbol(symbol: str) -> str:
    if symbol[0] in {"Z", "X"} and len(symbol) == 4:
        return symbol[1:]
    return symbol


class Api(ProviderBase):
    description = "Kraken (UK)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._api: Optional[krakenex.API] = None
        self._account_ccy = "EUR"

    def _account_description(self) -> Account:
        return Account(
            id="portfolio",
            name="Portfolio",
            iso_currency=CurrencyCode(self._account_ccy),
            type="investment",
        )

    def _iter_balances(self) -> Iterator[Tuple[str, float, float]]:
        price_fetcher = KrakenPriceFetcher(self._api)
        assert self._api is not None
        results = self._api.query_private("Balance")["result"]
        for symbol, units in results.items():
            units = float(units)
            if units > OWNERSHIP_UNITS_THRESHOLD:
                demangled_symbol = _demangle_symbol(symbol)
                if _is_cash(symbol):
                    rate = fx_market.get_rate(fx_market.Xccy(demangled_symbol, self._account_ccy))
                else:
                    rate = price_fetcher.get_last_price(demangled_symbol, self._account_ccy)
                yield symbol, units, units * rate

    def initialize(self) -> None:
        self._api = krakenex.API(
            key=self._credentials.api_key.get_secret_value(),
            secret=self._credentials.private_key.get_secret_value(),
        )
        results = self._api.query_private("Balance")
        if results["error"]:
            raise AuthenticationFailure(_format_error(results["error"]))

    def get_balances(self) -> Balances:
        balance = sum(value for (_, _, value) in self._iter_balances())
        return Balances(accounts=[BalanceEntry(account=self._account_description(), balance=balance)])

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account=self._account_description(),
                    assets=[
                        _make_asset(
                            symbol=symbol,
                            units=units,
                            value=value,
                            user_account_currency=self.user_account_currency,
                        )
                        for symbol, units, value in self._iter_balances()
                    ],
                )
            ]
        )


def _make_asset(
    symbol: str,
    units: float,
    value: float,
    user_account_currency: CurrencyCode,
) -> Asset:
    demangled_symbol = _demangle_symbol(symbol)
    if _is_cash(symbol):
        currency = CurrencyCode(demangled_symbol)
        return Asset.cash(
            currency=currency,
            is_domestic=currency == user_account_currency,
            amount=units,
        )
    else:
        return Asset(
            name=demangled_symbol,
            type="cryptocurrency",
            asset_class=AssetClass.crypto,
            asset_type=AssetType.crypto_currency,
            units=units,
            value=value,
        )


class KrakenPriceFetcher(object):
    class Error(FinbotError):
        pass

    def __init__(
        self,
        kraken_api: krakenex.API,
    ):
        self.api = kraken_api

    def get_last_price(
        self,
        source_crypto_asset: str,
        target_ccy: str,
    ) -> float:
        if source_crypto_asset == target_ccy:
            return 1.0
        pair_str = f"{source_crypto_asset}/{target_ccy}"
        pair = f"{source_crypto_asset}{target_ccy}"
        args = "Ticker", {"pair": pair}
        results = self.api.query_public(*args)
        if results["error"]:
            raise KrakenPriceFetcher.Error(f"{pair_str} " + _format_error(results["error"]))
        return float(results["result"][list(results["result"].keys())[0]]["c"][0])
