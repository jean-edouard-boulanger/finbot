import logging
import typing as t
from datetime import date, timedelta

import yfinance as yf

from finbot.core.schema import CurrencyCode

TickerType: t.TypeAlias = str
CacheKey: t.TypeAlias = tuple[TickerType, t.Literal["hist", "info"]]


def _hist_cache_key(ticker: TickerType) -> CacheKey:
    return ticker, "hist"


def _info_cache_key(ticker: TickerType) -> CacheKey:
    return ticker, "info"


class Market:
    def __init__(
        self,
        last_val_date: date,
        valuation_ccy: CurrencyCode,
    ):
        self.last_value_date: date = last_val_date
        self.valuation_ccy: CurrencyCode = valuation_ccy
        self._cache: dict[CacheKey, t.Any] = {}

    def get_fx_rate(self, domestic: CurrencyCode, foreign: CurrencyCode, as_of: date) -> float:
        if domestic == foreign:
            return 1.0
        ticker = f"{domestic}{foreign}=X"
        rev_ticker = f"{foreign}{domestic}=X"
        if _hist_cache_key(ticker) not in self._cache and _hist_cache_key(rev_ticker) in self._cache:
            return 1.0 / self.get_asset_value(rev_ticker, as_of)
        return self.get_asset_value(ticker, as_of)

    def get_asset_value(self, ticker: TickerType, as_of: date) -> float:
        cache_key = _hist_cache_key(ticker)
        if _hist_cache_key(ticker) not in self._cache:
            self._prefetch_and_cache_yfinance_hist_data(
                ticker=ticker,
                as_of=as_of,
            )
        result = self._cache[cache_key][as_of]
        assert isinstance(result, float)
        return result

    def get_ticker_info(self, ticker: TickerType) -> dict[str, t.Any]:
        cache_key = _info_cache_key(ticker)
        if cache_key not in self._cache:
            self._cache[cache_key] = yf.Ticker(ticker).info
        return t.cast(dict[str, t.Any], self._cache[cache_key])

    def get_ticker_currency(self, ticker: TickerType) -> CurrencyCode:
        result = self.get_ticker_info(ticker)["currency"]
        assert isinstance(result, str)
        return CurrencyCode(result)

    def _prefetch_and_cache_yfinance_hist_data(self, ticker: TickerType, as_of: date) -> None:
        start, end = as_of, self.last_value_date
        assert start <= end
        download_kwargs = dict(
            tickers=f"{ticker}",
            start=self._format_yfinance_date(start),
            end=self._format_yfinance_date(end),
            interval="1d",
        )
        logging.info(f"downloading yfinance data: {download_kwargs}")
        raw_data = yf.download(**download_kwargs)
        current_date = start
        result: dict[date, float] = {}
        last_value = None
        for index, row in raw_data.iterrows():
            while current_date <= index.date():
                last_value = float(row["Close"])
                assert last_value is not None
                result[current_date] = last_value
                current_date = current_date + timedelta(days=1)
        if last_value is not None:
            while current_date <= end:
                result[current_date] = last_value
                current_date = current_date + timedelta(days=1)
        self._cache[_hist_cache_key(ticker)] = result

    @staticmethod
    def _format_yfinance_date(d: date) -> str:
        return d.strftime("%Y-%m-%d")
