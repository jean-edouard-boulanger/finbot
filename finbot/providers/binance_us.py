from finbot import providers
from finbot.providers.errors import AuthFailure
from finbot.providers.support import CoinGeckoWrapper
from pycoingecko import CoinGeckoAPI
from binance.client import Client as Binance
from binance.exceptions import BinanceAPIException


class Credentials(object):
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key

    @property
    def user_id(self):
        return "<private>"

    @staticmethod
    def init(data):
        return Credentials(data["api_key"], data["secret_key"])


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
            "iso_currency": self._account_ccy
        }

    def authenticate(self, credentials):
        try:
            self._api = Binance(credentials.api_key, credentials.secret_key)
            self._api.get_account()
        except BinanceAPIException as e:
            raise AuthFailure(str(e))

    def _iter_balances(self):
        for entry in self._api.get_account()["balances"]:
            units = float(entry["free"]) + float(entry["locked"])
            if units > 0.00001:
                symbol = entry["asset"]
                value = units * self._spot_api.get_spot_cached(
                    symbol, self._account_ccy)
                yield symbol, units, value

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
                            "type": "crypto",
                            "units": units,
                            "value": value
                        }
                        for symbol, units, value in self._iter_balances()
                    ]
                }
            ]
        }
