from finbot import providers
from finbot.providers.errors import AuthFailure
import krakenex


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


def format_error(errors):
    return ", ".join(errors)


def classify_asset(symbol):
    if symbol.startswith("Z"):
        return "currency"
    return "crypto"


def format_symbol(symbol):
    return symbol[1:] if len(symbol) > 3 else symbol


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
            raise RuntimeError(f"{pair} " + format_error(results["error"]))
        return float(results["result"][list(results["result"].keys())[0]]["c"][0])


class Api(providers.Base):
    def __init__(self, *args, **kwargs):
        self.api = None
        self.account_ccy = "EUR"

    def _account_description(self):
        return {
            "id": "portfolio",
            "name": "Portfolio",
            "iso_currency": self.account_ccy
        }

    def _iter_balances(self):
        price_fetcher = KrakenPriceFetcher(self.api)
        results = self.api.query_private("Balance")["result"]
        for symbol, units in results.items():
            demangled_symbol = format_symbol(symbol)
            units = float(units)
            if units > 0.0:
                rate = price_fetcher.get_last_price(demangled_symbol, self.account_ccy)
                yield symbol, units, units * rate

    def authenticate(self, credentials):
        self.api = krakenex.API(credentials.api_key, credentials.private_key)
        results = self.api.query_private("Balance")
        if results["error"]:
            raise AuthFailure(format_error(results["error"]))

    def get_balances(self, *args, **kwargs):
        balance = sum(value for (_, _, value) in self._iter_balances())
        return {
            "accounts": [
                {
                    "account": self._account_description(),
                    "balance": balance
                }
            ]
        }

    def get_assets(self, *args, **kwargs):
        return {
            "accounts": [
                {
                    "account": self._account_description(),
                    "assets": [
                        {
                            "name": format_symbol(symbol),
                            "type": classify_asset(symbol),
                            "units": units,
                            "value": value
                        }
                    ]
                }
                for symbol, units, value in self._iter_balances()
            ]
        }