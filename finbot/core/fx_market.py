import logging
from dataclasses import dataclass
from typing import Optional, TypeAlias, cast

import requests
from cachetools import TTLCache, cached

from finbot.core.async_ import aexec
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


@cached(TTLCache(maxsize=1000, ttl=3600.0))
def _get_rates_for_base(base_ccy: CurrencyType) -> dict[CurrencyType, float]:
    api_key = get_freecurrencyapi_key()
    response = requests.get(f"https://api.freecurrencyapi.com/v1/latest?apikey={api_key}&base_currency={base_ccy}")
    response.raise_for_status()
    data = cast(dict[CurrencyType, float], response.json()["data"])
    return data


def get_rates(pairs: set[Xccy]) -> dict[Xccy, Optional[float]]:
    result: dict[Xccy, Optional[float]] = {}
    for pair in pairs:
        if pair.foreign == pair.domestic:
            result[pair] = 1.0
        else:
            rates = _get_rates_for_base(base_ccy=pair.foreign)
            rate = rates.get(pair.domestic)
            rate = 1.0 / rate if rate else None
            result[pair] = rate
    return result


async def async_get_rates(pairs: set[Xccy]) -> dict[Xccy, Optional[float]]:
    return await aexec(get_rates, pairs)


def get_rate(pair: Xccy) -> Optional[float]:
    return get_rates({pair}).get(pair)


async def async_get_rate(pair: Xccy) -> Optional[float]:
    return await aexec(get_rate, pair)
