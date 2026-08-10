import logging
import math
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, TypeAlias, get_args

import yfinance as yf
from cachetools import TTLCache, cached

from finbot.core.async_ import aexec
from finbot.core.errors import FinbotError
from finbot.core.schema import CurrencyCode
from finbot.core.utils import now_utc

logger = logging.getLogger(__name__)

QUOTE_CACHE_TTL = 3600.0
SEARCH_CACHE_TTL = 900.0
DEFAULT_SEARCH_RESULTS = 15
MAX_SEARCH_RESULTS = 50

SecurityKind: TypeAlias = Literal[
    "equity",
    "etf",
    "mutualfund",
    "index",
    "future",
    "currency",
    "cryptocurrency",
]
SECURITY_KINDS: tuple[SecurityKind, ...] = get_args(SecurityKind)

# Yahoo Finance searches one instrument type at a time, each behind its own `Lookup` method.
_LOOKUP_METHODS: dict[SecurityKind | None, str] = {
    None: "get_all",
    "equity": "get_stock",
    "etf": "get_etf",
    "mutualfund": "get_mutualfund",
    "index": "get_index",
    "future": "get_future",
    "currency": "get_currency",
    "cryptocurrency": "get_cryptocurrency",
}


class SecuritiesMarketError(FinbotError):
    pass


class UnknownSecurity(SecuritiesMarketError):
    def __init__(self, symbol: str) -> None:
        super().__init__(f"Could not find a security with symbol '{symbol}'")
        self.symbol = symbol


class SecuritiesSearchFailed(SecuritiesMarketError):
    def __init__(self, query: str) -> None:
        super().__init__(f"Could not search for securities matching '{query}'")
        self.query = query


@dataclass(frozen=True)
class SecurityQuote:
    symbol: str
    name: str | None
    currency: CurrencyCode
    price: float
    as_of: datetime


@dataclass(frozen=True)
class SecuritySearchResult:
    symbol: str
    name: str | None
    kind: SecurityKind | None
    exchange: str | None


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

    def search(
        self,
        query: str,
        kind: SecurityKind | None = None,
        limit: int = DEFAULT_SEARCH_RESULTS,
    ) -> tuple[SecuritySearchResult, ...]:
        """Search Yahoo Finance for securities matching a free-text query.

        The query matches both symbols and names, and results come back in Yahoo's own relevance
        order. `kind` narrows the search to a single instrument type; without it, every type is
        searched at once.
        """
        limit = max(1, min(limit, MAX_SEARCH_RESULTS))
        try:
            lookup = self._impl.Lookup(query)
            results = getattr(lookup, _LOOKUP_METHODS[kind])(count=limit)
        except Exception as e:
            raise SecuritiesSearchFailed(query) from e
        if results is None or results.empty:
            return ()
        return tuple(
            self._parse_search_result(symbol, row) for symbol, row in results.head(limit).to_dict("index").items()
        )

    @cached(TTLCache(maxsize=1_000, ttl=SEARCH_CACHE_TTL), lock=threading.Lock())
    def search_cached(
        self,
        query: str,
        kind: SecurityKind | None = None,
        limit: int = DEFAULT_SEARCH_RESULTS,
    ) -> tuple[SecuritySearchResult, ...]:
        return self.search(query, kind=kind, limit=limit)

    async def async_search(
        self,
        query: str,
        kind: SecurityKind | None = None,
        limit: int = DEFAULT_SEARCH_RESULTS,
    ) -> tuple[SecuritySearchResult, ...]:
        return await aexec(self.search, query, kind=kind, limit=limit)

    async def async_search_cached(
        self,
        query: str,
        kind: SecurityKind | None = None,
        limit: int = DEFAULT_SEARCH_RESULTS,
    ) -> tuple[SecuritySearchResult, ...]:
        return await aexec(self.search_cached, query, kind=kind, limit=limit)

    def __eq__(self, other: object) -> bool:
        # The cached lookups above are keyed on the instance, and callers routinely build a
        # throwaway `SecuritiesMarket()` per request: keying on identity would hand each of them a
        # cache of its own, which is the same as having none. Two markets talking to the same
        # backend are interchangeable.
        return isinstance(other, SecuritiesMarket) and other._impl is self._impl

    def __hash__(self) -> int:
        return hash(id(self._impl))

    @classmethod
    def _parse_search_result(cls, symbol: Any, row: dict[str, Any]) -> SecuritySearchResult:
        name = cls._clean(row.get("shortName"))
        return SecuritySearchResult(
            symbol=str(symbol),
            # Yahoo repeats the symbol as the name when it holds no better label for it.
            name=name if name != str(symbol) else None,
            kind=cls._parse_kind(row.get("quoteType")),
            exchange=cls._clean(row.get("exchange")),
        )

    @classmethod
    def _parse_kind(cls, value: Any) -> SecurityKind | None:
        kind = cls._clean(value)
        return kind if kind in SECURITY_KINDS else None

    @staticmethod
    def _clean(value: Any) -> str | None:
        """Turn a cell of a lookup result into a string, accounting for pandas' missing values."""
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        return str(value).strip() or None

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
