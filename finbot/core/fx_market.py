from finbot.core.errors import FinbotError
from finbot.core.environment import get_fcsapi_key
from finbot.core import tracer

from dataclasses import dataclass
from typing import Optional, Any
from requests import Response
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


class Error(FinbotError):
    pass


def _format_pair(pair: Xccy) -> str:
    return f"{pair.domestic}/{pair.foreign}"


def _format_pairs(pairs: set[Xccy]) -> str:
    return ",".join(_format_pair(pair) for pair in pairs)


def _handle_fcsapi_response(response: Response, resource: str) -> Any:
    response.raise_for_status()
    payload = response.json()
    print(tracer.current().name)
    tracer.current().set_output(payload)
    if "status" not in payload:
        raise Error(
            f"failure while querying fcsapi ({resource}): "
            f"missing 'status' in payload"
        )
    if not payload["status"]:
        raise Error(
            f"failure while querying fcsapi ({resource}): "
            f"{payload['msg']} (code: {payload['code']})"
        )
    if "response" not in payload:
        raise Error(
            f"failure while querying fcsapi ({resource}): "
            f"missing 'response' in payload"
        )
    return payload["response"]


def get_rates(pairs: set[Xccy]) -> dict[Xccy, Optional[float]]:
    pairs_str = _format_pairs(pairs)
    resource = f"{API_URL}/latest?symbol={pairs_str}"
    resource += f"&access_key={get_fcsapi_key()}"
    with tracer.sub_step(f"Query {pairs_str} rate(s) from fcsapi") as step:
        step.set_input({"resource": resource})
        response = requests.get(resource)
        rates_data = _handle_fcsapi_response(response, resource)
    rates: dict[Xccy, Optional[float]] = {
        Xccy(*entry["s"].split("/")): float(entry["c"]) for entry in rates_data
    }
    for pair in pairs:
        if pair not in rates:
            rates[pair] = None
    return rates


def get_rate(pair: Xccy) -> Optional[float]:
    return get_rates({pair}).get(pair)
