from finbot import providers
from finbot.providers.errors import AuthFailure
import krakenex


OWNERSHIP_UNITS_THRESHOLD = 0.00001


class Credentials(object):
    def __init__(self, api_key, private_key):
        self.api_key = api_key
        self.private_key = private_key

    @property
    def user_id(self):
        return "<private>"

    @staticmethod
    def init(data):
        return Credentials(data["api_key"], data["private_key"])


class Api(providers.Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._api = None
        self._account_ccy = "EUR"

    def _account_description(self):
        return {
            "id": "portfolio",
            "name": "Portfolio",
            "iso_currency": self._account_ccy,
            "type": "investment"
        }

    def _iter_balances(self):
        price_fetcher = KrakenPriceFetcher(self._api)
        results = self._api.query_private("Balance")["result"]
        for symbol, units in results.items():
            units = float(units)
            if units > OWNERSHIP_UNITS_THRESHOLD:
                demangled_symbol = _format_symbol(symbol)
                rate = price_fetcher.get_last_price(demangled_symbol, self._account_ccy)
                yield symbol, units, units * rate

    def authenticate(self, credentials):
        self._api = krakenex.API(credentials.api_key, credentials.private_key)
        results = self._api.query_private("Balance")
        if results["error"]:
            raise AuthFailure(_format_error(results["error"]))

    def get_balances(self):
        balance = sum(value for (_, _, value) in self._iter_balances())
        return {
            "accounts": [
                {
                    "account": self._account_description(),
                    "balance": balance
                }
            ]
        }

    def get_assets(self):
        return {
            "accounts": [
                {
                    "account": self._account_description(),
                    "assets": [
                        {
                            "name": _format_symbol(symbol),
                            "type": _classify_asset(symbol),
                            "units": units,
                            "value": value
                        }
                    ]
                }
                for symbol, units, value in self._iter_balances()
            ]
        }


def _format_error(errors):
    return ", ".join(errors)


def _classify_asset(symbol):
    if symbol.startswith("Z"):
        return "currency"
    return "crypto"


def _format_symbol(symbol):
    if symbol[0] in {"Z", "X"} and len(symbol) == 4:
        return symbol[1:]
    return symbol


class KrakenPriceFetcher(object):
    def __init__(self, kraken_api):
        self.api = kraken_api

    def get_last_price(self, source_crypto_asset, target_ccy):
        if source_crypto_asset == target_ccy:
            return 1.0
        pair = f"{source_crypto_asset}{target_ccy}"
        results = self.api.query_public("Ticker", {
            "pair": pair
        })
        if results["error"]:
            raise RuntimeError(f"{pair} " + _format_error(results["error"]))
        return float(results["result"][list(results["result"].keys())[0]]["c"][0])
