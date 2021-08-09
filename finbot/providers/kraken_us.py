from finbot import providers
from finbot.core.errors import FinbotError
from finbot.providers.errors import AuthenticationFailure
from finbot.core import tracer

import krakenex

from typing import Optional, Iterator, Tuple, Any


OWNERSHIP_UNITS_THRESHOLD = 0.00001


class Credentials(object):
    def __init__(self, api_key: str, private_key: str) -> None:
        self.api_key = api_key
        self.private_key = private_key

    @property
    def user_id(self) -> str:
        return "<private>"

    @staticmethod
    def init(data: dict[Any, Any]) -> "Credentials":
        return Credentials(data["api_key"], data["private_key"])


class Api(providers.Base):
    def __init__(self) -> None:
        super().__init__()
        self._api: Optional[krakenex.API] = None
        self._account_ccy = "EUR"

    def _account_description(self) -> providers.Account:
        return {
            "id": "portfolio",
            "name": "Portfolio",
            "iso_currency": self._account_ccy,
            "type": "investment",
        }

    def _iter_balances(self) -> Iterator[Tuple[str, float, float]]:
        price_fetcher = KrakenPriceFetcher(self._api)
        assert self._api is not None
        results = self._api.query_private("Balance")["result"]
        for symbol, units in results.items():
            units = float(units)
            if units > OWNERSHIP_UNITS_THRESHOLD:
                demangled_symbol = _format_symbol(symbol)
                rate = price_fetcher.get_last_price(demangled_symbol, self._account_ccy)
                yield symbol, units, units * rate

    def authenticate(self, credentials: Credentials) -> None:
        self._api = krakenex.API(credentials.api_key, credentials.private_key)
        results = self._api.query_private("Balance")
        if results["error"]:
            raise AuthenticationFailure(_format_error(results["error"]))

    def get_balances(self) -> providers.Balances:
        balance = sum(value for (_, _, value) in self._iter_balances())
        return {
            "accounts": [{"account": self._account_description(), "balance": balance}]
        }

    def get_assets(self) -> providers.Assets:
        return {
            "accounts": [
                {
                    "account": self._account_description(),
                    "assets": [
                        {
                            "name": _format_symbol(symbol),
                            "type": _classify_asset(symbol),
                            "units": units,
                            "value": value,
                        }
                    ],
                }
                for symbol, units, value in self._iter_balances()
            ]
        }


def _format_error(errors: list[str]) -> str:
    return ", ".join(errors)


def _classify_asset(symbol: str) -> str:
    if symbol.startswith("Z"):
        return "currency"
    return "crypto"


def _format_symbol(symbol: str) -> str:
    if symbol[0] in {"Z", "X"} and len(symbol) == 4:
        return symbol[1:]
    return symbol


class KrakenPriceFetcher(object):
    class Error(FinbotError):
        pass

    def __init__(self, kraken_api: krakenex.API):
        self.api = kraken_api

    def get_last_price(self, source_crypto_asset: str, target_ccy: str) -> float:
        if source_crypto_asset == target_ccy:
            return 1.0
        pair_str = f"{source_crypto_asset}/{target_ccy}"
        with tracer.sub_step(f"Query {pair_str} rate from Kraken") as step:
            pair = f"{source_crypto_asset}{target_ccy}"
            args = "Ticker", {"pair": pair}
            step.set_input(args)
            results = self.api.query_public(*args)
            step.set_output(results)
        if results["error"]:
            raise KrakenPriceFetcher.Error(
                f"{pair_str} " + _format_error(results["error"])
            )
        return float(results["result"][list(results["result"].keys())[0]]["c"][0])
