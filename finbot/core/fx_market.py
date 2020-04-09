from typing import Optional
from datetime import date
import requests
import json


API_URL = "https://api.exchangeratesapi.io"


def get_xccy_rate(domestic_ccy: str,
                  foreign_ccy: str,
                  fixing_date: Optional[date] = None) -> float:
    if domestic_ccy == foreign_ccy:
        return 1.0
    date_str = fixing_date.strftime("%Y-%m-%d") if fixing_date else "latest"
    response = requests.get(
        f"{API_URL}/{date_str}?base={domestic_ccy.upper()}&symbols={foreign_ccy.upper()}")
    data = json.loads(response.content.decode())
    if "error" in data:
        raise RuntimeError(data["error"])
    return float(data["rates"][foreign_ccy.upper()])
