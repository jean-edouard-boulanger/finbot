import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import yfinance as yf
from cachetools import TTLCache, cached

from finbot.core.async_ import aexec
from finbot.core.errors import FinbotError
from finbot.core.schema import CurrencyCode
from finbot.core.utils import now_utc

logger = logging.getLogger(__name__)

QUOTE_CACHE_TTL = 3600.0


class SecuritiesMarketError(FinbotError):
    pass


class UnknownSecurity(SecuritiesMarketError):
    def __init__(self, symbol: str) -> None:
        super().__init__(f"Could not find a security with symbol '{symbol}'")
        self.symbol = symbol


@dataclass(frozen=True)
class SecurityQuote:
    symbol: str
    name: str | None
    currency: CurrencyCode
    price: float
    as_of: datetime


class SecuritiesMarket(object):
    """Resolves securities spot prices via Yahoo Finance.

    Symbols are Yahoo Finance tickers, which cover a lot more than equities: `SGLN.L` (gold ETC),
    `GC=F` (gold futures), `BTC-USD`, `EURUSD=X`, market indices, etc.
    """

    def __init__(self, impl: Any = None):
        self._impl = impl or yf

    def get_quote(self, symbol: str, with_name: bool = False) -> SecurityQuote:
        """Get the latest quote for the provided symbol.

        `with_name` additionally resolves the security's display name, which requires a second
        (slower) call to Yahoo Finance: only use it in interactive contexts.
        """
        try:
            ticker = self._impl.Ticker(symbol)
        except Exception as e:
            raise UnknownSecurity(symbol) from e
        price, currency = self._get_price_and_currency(ticker, symbol)
        return SecurityQuote(
            symbol=symbol,
            name=self._get_name(ticker) if with_name else None,
            currency=currency,
            price=price,
            as_of=now_utc(),
        )

    @cached(TTLCache(maxsize=10_000, ttl=QUOTE_CACHE_TTL), lock=threading.Lock())
    def get_quote_cached(self, symbol: str, with_name: bool = False) -> SecurityQuote:
        return self.get_quote(symbol, with_name=with_name)

    async def async_get_quote(self, symbol: str, with_name: bool = False) -> SecurityQuote:
        return await aexec(self.get_quote, symbol, with_name=with_name)

    async def async_get_quote_cached(self, symbol: str, with_name: bool = False) -> SecurityQuote:
        return await aexec(self.get_quote_cached, symbol, with_name=with_name)

    @staticmethod
    def _get_price_and_currency(ticker: Any, symbol: str) -> tuple[float, CurrencyCode]:
        try:
            fast_info = ticker.fast_info
            raw_price = fast_info["lastPrice"]
            raw_currency = fast_info["currency"]
        except Exception as e:
            raise UnknownSecurity(symbol) from e
        if raw_price is None or raw_currency is None:
            raise UnknownSecurity(symbol)
        # `CurrencyCode` only normalises case when validated through pydantic, and Yahoo Finance is
        # not consistent about it, so it has to be done here.
        return float(raw_price), CurrencyCode(str(raw_currency).upper())

    @staticmethod
    def _get_name(ticker: Any) -> str | None:
        try:
            info = ticker.info
        except Exception:
            logger.warning("could not resolve security name", exc_info=True)
            return None
        name = info.get("longName") or info.get("shortName")
        return str(name) if name else None
