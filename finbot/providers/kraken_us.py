from typing import Any, Iterator, Optional, Tuple

import krakenex
from pydantic import BaseModel, SecretStr

from finbot.core import fx_market
from finbot.core.errors import FinbotError
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

OWNERSHIP_UNITS_THRESHOLD = 0.00001


class Credentials(BaseModel):
    api_key: SecretStr
    private_key: SecretStr


def _format_error(errors: list[str]) -> str:
    return ", ".join(errors)


def _is_currency(symbol: str) -> bool:
    return symbol.startswith("Z")


def _classify_asset(symbol: str) -> str:
    if _is_currency(symbol):
        return "currency"
    return "cryptocurrency"


def _demangle_symbol(symbol: str) -> str:
    if symbol[0] in {"Z", "X"} and len(symbol) == 4:
        return symbol[1:]
    return symbol


class Api(ProviderBase):
    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        self._api: Optional[krakenex.API] = None
        self._account_ccy = "EUR"

    @staticmethod
    def description() -> str:
        return "Kraken (UK)"

    @staticmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

    def _account_description(self) -> Account:
        return Account(
            id="portfolio",
            name="Portfolio",
            iso_currency=self._account_ccy,
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
                if _is_currency(symbol):
                    rate = fx_market.get_rate(
                        fx_market.Xccy(demangled_symbol, self._account_ccy)
                    )
                else:
                    rate = price_fetcher.get_last_price(
                        demangled_symbol, self._account_ccy
                    )
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
        return Balances(
            accounts=[
                BalanceEntry(account=self._account_description(), balance=balance)
            ]
        )

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account=self._account_description(),
                    assets=[
                        Asset(
                            name=_demangle_symbol(symbol),
                            type=_classify_asset(symbol),
                            units=units,
                            value=value,
                        )
                        for symbol, units, value in self._iter_balances()
                    ],
                )
            ]
        )


class KrakenPriceFetcher(object):
    class Error(FinbotError):
        pass

    def __init__(self, kraken_api: krakenex.API):
        self.api = kraken_api

    def get_last_price(self, source_crypto_asset: str, target_ccy: str) -> float:
        if source_crypto_asset == target_ccy:
            return 1.0
        pair_str = f"{source_crypto_asset}/{target_ccy}"
        pair = f"{source_crypto_asset}{target_ccy}"
        args = "Ticker", {"pair": pair}
        results = self.api.query_public(*args)
        if results["error"]:
            raise KrakenPriceFetcher.Error(
                f"{pair_str} " + _format_error(results["error"])
            )
        return float(results["result"][list(results["result"].keys())[0]]["c"][0])
