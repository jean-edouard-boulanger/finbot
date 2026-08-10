from typing import Any

import pandas as pd
import pytest

from finbot.core.securities_market import (
    SecuritiesMarket,
    SecuritiesSearchFailed,
    UnknownSecurity,
)


class FakeTicker:
    def __init__(self, fast_info: Any, info: Any = None):
        self.fast_info = fast_info
        self._info = info if info is not None else {}

    @property
    def info(self) -> Any:
        if isinstance(self._info, Exception):
            raise self._info
        return self._info


class FakeLookup:
    """Stands in for `yfinance.Lookup`, whose getters return one dataframe indexed by symbol."""

    def __init__(self, results: dict[str, list[dict[str, Any]]]):
        self._results = results

    def _frame(self, lookup_type: str, count: int) -> pd.DataFrame:
        rows = self._results.get(lookup_type, [])
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows[:count]).set_index("symbol")

    def get_all(self, count: int = 25) -> pd.DataFrame:
        return self._frame("all", count)

    def get_etf(self, count: int = 25) -> pd.DataFrame:
        return self._frame("etf", count)


class FakeYFinance:
    def __init__(
        self,
        tickers: dict[str, FakeTicker],
        lookups: dict[str, dict[str, list[dict[str, Any]]]] | None = None,
        failing_queries: set[str] | None = None,
    ):
        self._tickers = tickers
        self._lookups = lookups or {}
        self._failing_queries = failing_queries or set()
        self.lookup_calls: list[str] = []

    def Ticker(self, symbol: str) -> FakeTicker:  # noqa: N802 (mirrors the yfinance API)
        if symbol not in self._tickers:
            raise KeyError(symbol)
        return self._tickers[symbol]

    def Lookup(self, query: str) -> FakeLookup:  # noqa: N802 (mirrors the yfinance API)
        self.lookup_calls.append(query)
        if query in self._failing_queries:
            raise RuntimeError("Yahoo Finance is currently down")
        return FakeLookup(self._lookups.get(query, {}))


class RaisingFastInfo:
    def __getitem__(self, key: str) -> Any:
        raise KeyError(key)


# Shaped like what Yahoo Finance actually returns: ranked, with columns missing on some rows.
GOLD_RESULTS = {
    "all": [
        {"symbol": "GLD", "shortName": "SPDR Gold Shares", "quoteType": "etf", "exchange": "PCX"},
        {"symbol": "GC=F", "shortName": "Gold Dec 26", "quoteType": "future", "exchange": "CMX"},
        {"symbol": "0P00019HF1.SA", "shortName": "0P00019HF1.SA", "quoteType": "mutualfund", "exchange": "SAO"},
        {"symbol": "GLDX", "quoteType": "ecnquote"},
    ],
    "etf": [
        {"symbol": "GLD", "shortName": "SPDR Gold Shares", "quoteType": "etf", "exchange": "PCX"},
        {"symbol": "SGLN.L", "shortName": "ISHARES PHYSICAL METALS PLC", "quoteType": "etf", "exchange": "LSE"},
    ],
}


@pytest.fixture(scope="function")
def yahoo() -> FakeYFinance:
    return FakeYFinance(
        tickers={},
        lookups={"gold": GOLD_RESULTS, "nothing at all": {}},
        failing_queries={"boom"},
    )


@pytest.fixture(scope="function")
def searchable_market(yahoo: FakeYFinance) -> SecuritiesMarket:
    return SecuritiesMarket(impl=yahoo)


@pytest.fixture(scope="function")
def market() -> SecuritiesMarket:
    return SecuritiesMarket(
        impl=FakeYFinance(
            {
                "GC=F": FakeTicker(
                    fast_info={"lastPrice": 4049.1, "currency": "USD"},
                    info={"longName": "Gold Dec 26", "shortName": "Gold"},
                ),
                "SGLN.L": FakeTicker(
                    fast_info={"lastPrice": 55.2, "currency": "gbp"},
                    info={"shortName": "iShares Physical Gold"},
                ),
                "NOINFO": FakeTicker(
                    fast_info={"lastPrice": 1.0, "currency": "EUR"},
                    info=RuntimeError("no info available"),
                ),
                "NOPRICE": FakeTicker(fast_info={"lastPrice": None, "currency": "USD"}),
                "BROKEN": FakeTicker(fast_info=RaisingFastInfo()),
            }
        )
    )


class TestGetQuote:
    def test_resolves_price_and_currency(self, market: SecuritiesMarket):
        quote = market.get_quote("GC=F")
        assert quote.symbol == "GC=F"
        assert quote.price == 4049.1
        assert quote.currency == "USD"
        assert quote.as_of is not None

    def test_does_not_resolve_name_by_default(self, market: SecuritiesMarket):
        assert market.get_quote("GC=F").name is None

    def test_resolves_long_name_when_requested(self, market: SecuritiesMarket):
        assert market.get_quote("GC=F", with_name=True).name == "Gold Dec 26"

    def test_falls_back_to_short_name(self, market: SecuritiesMarket):
        assert market.get_quote("SGLN.L", with_name=True).name == "iShares Physical Gold"

    def test_normalizes_currency_case(self, market: SecuritiesMarket):
        assert market.get_quote("SGLN.L").currency == "GBP"

    def test_name_resolution_failure_is_not_fatal(self, market: SecuritiesMarket):
        quote = market.get_quote("NOINFO", with_name=True)
        assert quote.name is None
        assert quote.price == 1.0

    def test_unknown_symbol_raises(self, market: SecuritiesMarket):
        with pytest.raises(UnknownSecurity):
            market.get_quote("NOPE")

    def test_missing_price_raises(self, market: SecuritiesMarket):
        with pytest.raises(UnknownSecurity):
            market.get_quote("NOPRICE")

    def test_broken_fast_info_raises(self, market: SecuritiesMarket):
        with pytest.raises(UnknownSecurity):
            market.get_quote("BROKEN")


class TestSearch:
    def test_returns_results_in_yahoo_order(self, searchable_market: SecuritiesMarket):
        results = searchable_market.search("gold")
        assert [result.symbol for result in results] == ["GLD", "GC=F", "0P00019HF1.SA", "GLDX"]

    def test_maps_name_kind_and_exchange(self, searchable_market: SecuritiesMarket):
        result = searchable_market.search("gold")[0]
        assert result.name == "SPDR Gold Shares"
        assert result.kind == "etf"
        assert result.exchange == "PCX"

    def test_drops_name_repeating_the_symbol(self, searchable_market: SecuritiesMarket):
        result = searchable_market.search("gold")[2]
        assert result.symbol == "0P00019HF1.SA"
        assert result.name is None

    def test_tolerates_missing_and_unknown_fields(self, searchable_market: SecuritiesMarket):
        result = searchable_market.search("gold")[3]
        assert result.symbol == "GLDX"
        assert result.name is None
        assert result.exchange is None
        # Yahoo has quote types Finbot does not model, and they must not fail the whole search.
        assert result.kind is None

    def test_kind_narrows_the_search(self, searchable_market: SecuritiesMarket):
        results = searchable_market.search("gold", kind="etf")
        assert [result.symbol for result in results] == ["GLD", "SGLN.L"]

    def test_limit_truncates_results(self, searchable_market: SecuritiesMarket):
        assert len(searchable_market.search("gold", limit=2)) == 2

    def test_limit_is_capped(self, searchable_market: SecuritiesMarket):
        assert len(searchable_market.search("gold", limit=10_000)) == 4

    def test_no_match_returns_nothing(self, searchable_market: SecuritiesMarket):
        assert searchable_market.search("nothing at all") == ()

    def test_unreachable_provider_raises(self, searchable_market: SecuritiesMarket):
        with pytest.raises(SecuritiesSearchFailed):
            searchable_market.search("boom")

    def test_cached_search_only_hits_yahoo_once(self, searchable_market: SecuritiesMarket, yahoo: FakeYFinance):
        first = searchable_market.search_cached("gold")
        second = searchable_market.search_cached("gold")
        assert first is second
        assert yahoo.lookup_calls == ["gold"]

    def test_cache_is_shared_across_markets_on_the_same_backend(
        self, searchable_market: SecuritiesMarket, yahoo: FakeYFinance
    ):
        # Callers build a throwaway market per request: they must still share one cache.
        searchable_market.search_cached("gold")
        SecuritiesMarket(impl=yahoo).search_cached("gold")
        assert yahoo.lookup_calls == ["gold"]


class TestAsyncSearch:
    @pytest.mark.asyncio
    async def test_async_search(self, searchable_market: SecuritiesMarket):
        results = await searchable_market.async_search("gold")
        assert [result.symbol for result in results] == ["GLD", "GC=F", "0P00019HF1.SA", "GLDX"]

    @pytest.mark.asyncio
    async def test_async_search_cached(self, searchable_market: SecuritiesMarket, yahoo: FakeYFinance):
        first = await searchable_market.async_search_cached("gold", kind="etf")
        second = await searchable_market.async_search_cached("gold", kind="etf")
        assert first is second
        assert yahoo.lookup_calls == ["gold"]


class TestAsyncGetQuote:
    @pytest.mark.asyncio
    async def test_async_get_quote(self, market: SecuritiesMarket):
        quote = await market.async_get_quote("GC=F")
        assert quote.price == 4049.1

    @pytest.mark.asyncio
    async def test_async_get_quote_cached(self, market: SecuritiesMarket):
        first = await market.async_get_quote_cached("GC=F")
        second = await market.async_get_quote_cached("GC=F")
        assert first is second
