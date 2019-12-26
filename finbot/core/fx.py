import requests
import json


API_URL = "https://api.exchangeratesapi.io"


def get_xccy_rate(domestic_ccy, foreign_ccy):
    def get_fx_rate_impl(home_ccy, foreign_ccy):
        if home_ccy == foreign_ccy:
            return 1.0
        response = requests.get(
            f"{API_URL}/latest?base={domestic_ccy.upper()}&symbols={foreign_ccy.upper()}")
        data = json.loads(response.content.decode())
        if "error" in data:
            raise RuntimeError(data["error"])
        return float(data["rates"][foreign_ccy.upper()])
    return get_fx_rate_impl(domestic_ccy, foreign_ccy)
