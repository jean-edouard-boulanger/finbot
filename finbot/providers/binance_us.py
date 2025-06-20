from typing import Any, AsyncGenerator

from binance.client import Client as Binance
from binance.exceptions import BinanceAPIException
from pydantic import SecretStr

from finbot.core.async_ import acollect, aexec
from finbot.core.crypto_market import CryptoMarket
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError
from finbot.providers.schema import Account, AccountType, Asset, AssetClass, Assets, AssetsEntry, AssetType

OWNERSHIP_UNITS_THRESHOLD = 0.00001
RECV_WINDOW = 60 * 1000


class Credentials(BaseModel):
    api_key: SecretStr
    secret_key: SecretStr


class Api(ProviderBase):
    description = "Binance (US)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._account_ccy = CurrencyCode.validate("USD")
        self._crypto_market = CryptoMarket()
        self._api: Binance | None = None

    async def _get_account(self) -> dict[str, Any]:
        assert self._api is not None
        account: dict[str, Any] = await aexec(self._api.get_account, recvWindow=RECV_WINDOW)
        return account

    def _account_description(self) -> Account:
        return Account(
            id="portfolio",
            name="Portfolio",
            iso_currency=self._account_ccy,
            type=AccountType.investment,
            sub_type="crypto exchange",
        )

    async def initialize(self) -> None:
        try:
            self._api = Binance(
                self._credentials.api_key.get_secret_value(),
                self._credentials.secret_key.get_secret_value(),
            )
            await self._get_account()
        except BinanceAPIException as e:
            raise AuthenticationError(str(e))

    async def get_accounts(self) -> list[Account]:
        return [self._account_description()]

    async def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=self._account_description().id,
                    items=await acollect(self._iter_assets()),
                )
            ]
        )

    async def _iter_assets(self) -> AsyncGenerator[Asset]:
        for entry in (await self._get_account())["balances"]:
            units = float(entry["free"]) + float(entry["locked"])
            if units > OWNERSHIP_UNITS_THRESHOLD:
                symbol = entry["asset"]
                value = units * await self._crypto_market.async_get_spot_cached(symbol, self._account_ccy)
                yield Asset(
                    name=symbol,
                    type="cryptocurrency",
                    asset_class=AssetClass.crypto,
                    asset_type=AssetType.crypto_currency,
                    units=units,
                    value_in_account_ccy=value,
                    currency=self._account_ccy,
                )
