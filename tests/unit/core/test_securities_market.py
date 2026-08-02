from typing import Any

import pytest

from finbot.core.securities_market import SecuritiesMarket, UnknownSecurity


class FakeTicker:
    def __init__(self, fast_info: Any, info: Any = None):
        self.fast_info = fast_info
        self._info = info if info is not None else {}

    @property
    def info(self) -> Any:
        if isinstance(self._info, Exception):
            raise self._info
        return self._info


class FakeYFinance:
    def __init__(self, tickers: dict[str, FakeTicker]):
        self._tickers = tickers

    def Ticker(self, symbol: str) -> FakeTicker:  # noqa: N802 (mirrors the yfinance API)
        if symbol not in self._tickers:
            raise KeyError(symbol)
        return self._tickers[symbol]


class RaisingFastInfo:
    def __getitem__(self, key: str) -> Any:
        raise KeyError(key)


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
