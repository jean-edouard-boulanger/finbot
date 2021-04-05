from finbot.core.environment import get_currconv_api_key

from dataclasses import dataclass
from typing import Optional
from datetime import date
import requests


API_URL = "https://free.currconv.com/api/v7"


@dataclass(frozen=True, eq=True)
class Xccy(object):
    domestic: str
    foreign: str

    def __str__(self) -> str:
        return f"{self.domestic}{self.foreign}"

    def serialize(self) -> dict[str, str]:
        return {"domestic": self.domestic, "foreign": self.foreign}


def _get_api_key() -> str:
    return get_currconv_api_key()


def _format_pair(pair: Xccy) -> str:
    return f"{pair.domestic}_{pair.foreign}"


def _format_pairs(pairs: set[Xccy]) -> str:
    return ",".join(_format_pair(pair) for pair in pairs)


def _format_date(dt: date) -> str:
    return dt.strftime("%Y-%m-%d")


def get_rates(
    pairs: set[Xccy], fixing_date: Optional[date] = None
) -> dict[Xccy, Optional[float]]:
    resource_url = f"{API_URL}/convert?q={_format_pairs(pairs)}&compact=ultra"
    if fixing_date:
        resource_url += f"&date={_format_date(fixing_date)}"
    resource_url += f"&apiKey={_get_api_key()}"
    resp = requests.get(resource_url)
    data = resp.json()
    return {xccy: data.get(_format_pair(xccy)) for xccy in pairs}


def get_rate(pair: Xccy, fixing_date: Optional[date] = None) -> Optional[float]:
    return get_rates({pair}, fixing_date).get(pair)
