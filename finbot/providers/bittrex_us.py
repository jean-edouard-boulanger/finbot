from finbot import providers
from finbot.core.crypto_market import CoinGeckoWrapper
from finbot.providers.errors import AuthFailure

from pycoingecko import CoinGeckoAPI
from bittrex.bittrex import Bittrex

from typing import Optional, Iterator, Tuple


OWNERSHIP_UNITS_THRESHOLD = 0.00001
BITTREX_REWARDS_TOKEN = "BTXCRD"


class Credentials(object):
    def __init__(self, api_key: str, private_key: str):
        self.api_key = api_key
        self.private_key = private_key

    @property
    def user_id(self) -> str:
        return "<private>"

    @staticmethod
    def init(data: dict[str, str]) -> "Credentials":
        return Credentials(data["api_key"], data["private_key"])


class Api(providers.Base):
    def __init__(self) -> None:
        super().__init__()
        self._account_ccy = "USD"
        self._spot_api = CoinGeckoWrapper(CoinGeckoAPI())
        self._api: Optional[Bittrex] = None

    def _account_description(self) -> providers.Account:
        return {
            "id": "portfolio",
            "name": "Portfolio",
            "iso_currency": self._account_ccy,
            "type": "investment",
        }

    def _iter_balances(self) -> Iterator[Tuple[str, float, float]]:
        assert self._api is not None
        for entry in self._api.get_balances()["result"]:
            units = entry["Available"]
            symbol = entry["Currency"]
            if units > OWNERSHIP_UNITS_THRESHOLD and symbol != BITTREX_REWARDS_TOKEN:
                value = units * self._spot_api.get_spot_cached(
                    symbol, self._account_ccy
                )
                yield symbol, units, value

    def authenticate(self, credentials: Credentials) -> None:
        self._api = Bittrex(credentials.api_key, credentials.private_key)
        results = self._api.get_balances()
        if not results["success"]:
            raise AuthFailure(results["message"])

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
                            "name": symbol,
                            "type": "cryptocurrency",
                            "units": units,
                            "value": value,
                        }
                        for symbol, units, value in self._iter_balances()
                    ],
                }
            ]
        }
