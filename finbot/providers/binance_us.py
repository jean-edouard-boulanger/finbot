from finbot import providers
from finbot.providers.errors import AuthenticationFailure
from finbot.core.crypto_market import CoinGeckoWrapper

from pycoingecko import CoinGeckoAPI
from binance.client import Client as Binance
from binance.exceptions import BinanceAPIException

from typing import Any, Optional, Iterator, Tuple


OWNERSHIP_UNITS_THRESHOLD = 0.00001
RECV_WINDOW = 60 * 1000


class Credentials(object):
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key

    @property
    def user_id(self) -> str:
        return "<private>"

    @staticmethod
    def init(data: dict[Any, Any]) -> "Credentials":
        return Credentials(data["api_key"], data["secret_key"])


class Api(providers.Base):
    def __init__(self) -> None:
        super().__init__()
        self._account_ccy = "USD"
        self._spot_api = CoinGeckoWrapper(CoinGeckoAPI())
        self._api: Optional[Binance] = None

    def _get_account(self) -> dict[Any, Any]:
        assert self._api is not None
        account: dict[Any, Any] = self._api.get_account(recvWindow=RECV_WINDOW)
        return account

    def _account_description(self) -> providers.Account:
        return {
            "id": "portfolio",
            "name": "Portfolio",
            "iso_currency": self._account_ccy,
            "type": "investment",
        }

    def authenticate(self, credentials: Credentials) -> None:
        try:
            self._api = Binance(credentials.api_key, credentials.secret_key)
            self._get_account()
        except BinanceAPIException as e:
            raise AuthenticationFailure(str(e))

    def _iter_balances(self) -> Iterator[Tuple[str, float, float]]:
        for entry in self._get_account()["balances"]:
            units = float(entry["free"]) + float(entry["locked"])
            if units > OWNERSHIP_UNITS_THRESHOLD:
                symbol = entry["asset"]
                value = units * self._spot_api.get_spot_cached(
                    symbol, self._account_ccy
                )
                yield symbol, units, value

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
