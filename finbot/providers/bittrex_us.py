from finbot import providers
from finbot.core.crypto_market import CoinGeckoWrapper
from finbot.providers.errors import AuthFailure
from pycoingecko import CoinGeckoAPI
from bittrex.bittrex import Bittrex


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
        self._account_ccy = "USD"
        self._spot_api = CoinGeckoWrapper(CoinGeckoAPI())
        self._api = None

    def _account_description(self):
        return {
            "id": "portfolio",
            "name": "Portfolio",
            "iso_currency": self._account_ccy,
            "type": "investment"
        }

    def _iter_balances(self):
        for entry in self._api.get_balances()["result"]:
            units = entry["Available"]
            if units > OWNERSHIP_UNITS_THRESHOLD:
                symbol = entry["Currency"]
                value = units * self._spot_api.get_spot_cached(
                    symbol, self._account_ccy)
                yield symbol, units, value

    def authenticate(self, credentials):
        self._api = Bittrex(credentials.api_key, credentials.private_key)
        results = self._api.get_balances()
        if not results["success"]:
            raise AuthFailure(results["message"])

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
                            "name": symbol,
                            "type": "cryptocurrency",
                            "units": units,
                            "value": value
                        }
                        for symbol, units, value in self._iter_balances()
                    ]
                }
            ]
        }
