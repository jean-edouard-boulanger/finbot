from typing import Any, Iterator, Optional, Tuple

from binance.client import Client as Binance
from binance.exceptions import BinanceAPIException
from pycoingecko import CoinGeckoAPI
from pydantic import BaseModel, SecretStr

from finbot.core import schema as core_schema
from finbot.core.crypto_market import CoinGeckoWrapper
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
RECV_WINDOW = 60 * 1000


class Credentials(BaseModel):
    api_key: SecretStr
    secret_key: SecretStr


class Api(ProviderBase):
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
    def create(
        authentication_payload: core_schema.CredentialsPayloadType, **kwargs: Any
    ) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

    def _get_account(self) -> dict[Any, Any]:
        assert self._api is not None
        account: dict[Any, Any] = self._api.get_account(recvWindow=RECV_WINDOW)
        return account

    def _account_description(self) -> Account:
        return Account(
            id="portfolio",
            name="Portfolio",
            iso_currency=self._account_ccy,
            type="investment",
        )

    def initialize(self) -> None:
        try:
            self._api = Binance(
                self._credentials.api_key.get_secret_value(),
                self._credentials.secret_key.get_secret_value(),
            )
            self._get_account()
        except BinanceAPIException as e:
            raise AuthenticationFailure(str(e))

    def _iter_holdings(self) -> Iterator[Tuple[str, float, float]]:
        for entry in self._get_account()["balances"]:
            units = float(entry["free"]) + float(entry["locked"])
            if units > OWNERSHIP_UNITS_THRESHOLD:
                symbol = entry["asset"]
                value = units * self._spot_api.get_spot_cached(
                    symbol, self._account_ccy
                )
                yield symbol, units, value

    def get_balances(self) -> Balances:
        balance = sum(value for (_, _, value) in self._iter_holdings())
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
                            name=symbol, type="cryptocurrency", units=units, value=value
                        )
                        for symbol, units, value in self._iter_holdings()
                    ],
                )
            ]
        )
