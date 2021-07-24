from finbot.core.environment import get_fcsapi_key

from dataclasses import dataclass
from typing import Optional
import requests


API_URL = "https://fcsapi.com/api-v3/forex"


@dataclass(frozen=True, eq=True)
class Xccy(object):
    domestic: str
    foreign: str

    def __str__(self) -> str:
        return f"{self.domestic}{self.foreign}"

    def serialize(self) -> dict[str, str]:
        return {"domestic": self.domestic, "foreign": self.foreign}


def _format_pair(pair: Xccy) -> str:
    return f"{pair.domestic}/{pair.foreign}"


def _format_pairs(pairs: set[Xccy]) -> str:
    return ",".join(_format_pair(pair) for pair in pairs)


def get_rates(pairs: set[Xccy]) -> dict[Xccy, Optional[float]]:
    resource_url = f"{API_URL}/latest?symbol={_format_pairs(pairs)}"
    resource_url += f"&access_key={get_fcsapi_key()}"
    resp = requests.get(resource_url)
    data = resp.json()["response"]
    return {Xccy(*entry["s"].split("/")): entry["c"] for entry in data}


def get_rate(pair: Xccy) -> Optional[float]:
    return get_rates({pair}).get(pair)
