import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, TypeAlias, cast

import requests

from finbot.core.environment import get_freecurrencyapi_key
from finbot.core.errors import FinbotError

logger = logging.getLogger(__name__)


CurrencyType: TypeAlias = str


@dataclass(frozen=True, eq=True)
class Xccy(object):
    domestic: CurrencyType
    foreign: CurrencyType

    def __str__(self) -> str:
        return f"{self.domestic}{self.foreign}"

    def serialize(self) -> dict[str, str]:
        return {"domestic": self.domestic, "foreign": self.foreign}


class Error(FinbotError):
    pass


class Client:
    @dataclass(frozen=True)
    class _CacheEntry:
        expiry: datetime
        data: dict[CurrencyType, float]

    def __init__(self, api_key: str, cache_ttl: timedelta | None = None):
        self._api_key = api_key
        self._cache_ttl = cache_ttl or timedelta(hours=1)
        self._cache: dict[CurrencyType, Client._CacheEntry] = {}

    def get_rates_for_base(self, base_ccy: CurrencyType) -> dict[CurrencyType, float]:
        if cache_entry := self._cache.get(base_ccy):
            if cache_entry.expiry > datetime.now():
                logger.debug("cache hit for base_ccy=%s", base_ccy)
                return cache_entry.data
        response = requests.get(
            f"https://api.freecurrencyapi.com/v1/latest?apikey={self._api_key}&base_currency={base_ccy}"
        )
        response.raise_for_status()
        data = cast(dict[CurrencyType, float], response.json()["data"])
        self._cache[base_ccy] = self._CacheEntry(expiry=datetime.now() + self._cache_ttl, data=data)
        return data


_CLIENT = None


def _get_shared_client() -> Client:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = Client(api_key=get_freecurrencyapi_key())
    return _CLIENT


def get_rates(pairs: set[Xccy]) -> dict[Xccy, Optional[float]]:
    result: dict[Xccy, Optional[float]] = {}
    for pair in pairs:
        if pair.foreign == pair.domestic:
            result[pair] = 1.0
        else:
            rates = _get_shared_client().get_rates_for_base(base_ccy=pair.foreign)
            rate = rates.get(pair.domestic)
            rate = 1.0 / rate if rate else None
            result[pair] = rate
    return result


def get_rate(pair: Xccy) -> Optional[float]:
    return get_rates({pair}).get(pair)
