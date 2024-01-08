from typing import Any, Generator

import krakenex

from finbot.core.errors import FinbotError
from finbot.core.pydantic_ import SecretStr
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    AssetClass,
    Assets,
    AssetsEntry,
    AssetType,
)

OWNERSHIP_UNITS_THRESHOLD = 0.00001
KRAKEN_CASH_SYMBOL_PREFIX = "Z"
KRAKEN_CRYPTOCURRENCY_SYMBOL_PREFIX = "X"

SchemaNamespace = "KrakenProvider"


class Credentials(BaseModel):
    api_key: SecretStr
    private_key: SecretStr


def _format_error(errors: list[str]) -> str:
    return ", ".join(errors)


def _is_cash(symbol: str) -> bool:
    return symbol.startswith(KRAKEN_CASH_SYMBOL_PREFIX)


def _demangle_symbol(symbol: str) -> str:
    if symbol[0] in {KRAKEN_CASH_SYMBOL_PREFIX, KRAKEN_CRYPTOCURRENCY_SYMBOL_PREFIX} and len(symbol) > 3:
        return symbol[1:]
    return symbol


class Api(ProviderBase):
    description = "Kraken (UK)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._api: krakenex.API | None = None
        self._account_ccy = CurrencyCode("EUR")

    def _account_description(self) -> Account:
        return Account(
            id="portfolio",
            name="Portfolio",
            iso_currency=CurrencyCode(self._account_ccy),
            type=AccountType.investment,
        )

    def _iter_assets(self) -> Generator[Asset, None, None]:
        price_fetcher = KrakenPriceFetcher(self._api)
        assert self._api is not None
        results = self._api.query_private("Balance")["result"]
        for symbol, units in results.items():
            units = float(units)
            if units > OWNERSHIP_UNITS_THRESHOLD:
                demangled_symbol = _demangle_symbol(symbol)
                if _is_cash(symbol):
                    currency_code = CurrencyCode.validate(demangled_symbol)
                    yield Asset.cash(
                        currency=currency_code,
                        is_domestic=currency_code == self.user_account_currency,
                        amount=units,
                    )
                else:
                    rate = price_fetcher.get_last_price(demangled_symbol, self._account_ccy)
                    yield Asset(
                        name=demangled_symbol,
                        type="cryptocurrency",  # deprecated
                        asset_class=AssetClass.crypto,
                        asset_type=AssetType.crypto_currency,
                        units=units,
                        value_in_account_ccy=units * rate,
                        currency=self._account_ccy,
                    )

    def initialize(self) -> None:
        self._api = krakenex.API(
            key=self._credentials.api_key.get_secret_value(),
            secret=self._credentials.private_key.get_secret_value(),
        )
        results = self._api.query_private("Balance")
        if results["error"]:
            raise AuthenticationError(_format_error(results["error"]))

    def get_accounts(self) -> list[Account]:
        return [self._account_description()]

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=self._account_description().id,
                    items=list(self._iter_assets()),
                )
            ]
        )


class KrakenPriceFetcher(object):
    class Error(FinbotError):
        pass

    def __init__(
        self,
        kraken_api: krakenex.API,
    ):
        self.api = kraken_api

    def get_last_price(
        self,
        source_crypto_asset: str,
        target_ccy: str,
    ) -> float:
        if source_crypto_asset == target_ccy:
            return 1.0
        pair_str = f"{source_crypto_asset}/{target_ccy}"
        pair = f"{source_crypto_asset}{target_ccy}"
        args = "Ticker", {"pair": pair}
        results = self.api.query_public(*args)
        if results["error"]:
            raise KrakenPriceFetcher.Error(f"{pair_str} " + _format_error(results["error"]))
        return float(results["result"][list(results["result"].keys())[0]]["c"][0])
