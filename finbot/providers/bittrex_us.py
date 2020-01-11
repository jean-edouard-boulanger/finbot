from finbot import providers
from finbot.providers.errors import AuthFailure
from pycoingecko import CoinGeckoAPI
from bittrex.bittrex import Bittrex
import requests
import json


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


class CoinGeckoWrapper(object):
    def __init__(self, coingecko_api: CoinGeckoAPI):
        self.api = coingecko_api
        self._symbols_to_id = {
            entry["symbol"]: entry["id"]
            for entry in self.api.get_coins_list()
        }

    def get_spot(self, source_crypto_ccy: str, target_ccy: str):
        target_ccy = target_ccy.lower()
        coin_id = self._symbols_to_id[source_crypto_ccy.lower()]
        result = self.api.get_price(coin_id, target_ccy)
        if coin_id not in result:
            raise RuntimeError(f"no spot for {coin_id}")
        return result[coin_id][target_ccy]


class Api(providers.Base):
    def __init__(self, *args, **kwargs):
        self.api = None
        self.account_ccy = "USD"

    def _account_description(self):
        return {
            "id": "portfolio",
            "name": "Portfolio",
            "iso_currency": self.account_ccy
        }

    def _iter_balances(self):
        spot_api = CoinGeckoWrapper(CoinGeckoAPI())
        for entry in self.api.get_balances()["result"]:
            symbol = entry["Currency"]
            units = entry["Available"]
            value = units * spot_api.get_spot(symbol, self.account_ccy)
            yield symbol, units, value

    def authenticate(self, credentials):
        self.api = Bittrex(credentials.api_key, credentials.private_key)
        results = self.api.get_balances()
        if not results["success"]:
            raise AuthFailure(results["message"])

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
                            "name": symbol,
                            "type": "crypto",
                            "units": units,
                            "value": value
                        }
                    ]
                }
                for symbol, units, value in self._iter_balances()
            ]
        }
