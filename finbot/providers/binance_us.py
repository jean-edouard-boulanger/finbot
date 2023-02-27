from typing import Any, Iterator, Optional, Tuple

from binance.client import Client as Binance
from binance.exceptions import BinanceAPIException
from pycoingecko import CoinGeckoAPI
from pydantic import BaseModel, SecretStr

from finbot import providers
from finbot.core.crypto_market import CoinGeckoWrapper
from finbot.providers.errors import AuthenticationFailure

OWNERSHIP_UNITS_THRESHOLD = 0.00001
RECV_WINDOW = 60 * 1000


class Credentials(BaseModel):
    api_key: SecretStr
    secret_key: SecretStr


class Api(providers.Base):
    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        self._account_ccy = "USD"
        self._spot_api = CoinGeckoWrapper(CoinGeckoAPI())
        self._api: Optional[Binance] = None

    @staticmethod
    def description() -> str:
        return "Binance (US)"

    @staticmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

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

    def initialize(self) -> None:
        try:
            self._api = Binance(
                self._credentials.api_key.get_secret_value(),
                self._credentials.secret_key.get_secret_value(),
            )
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
