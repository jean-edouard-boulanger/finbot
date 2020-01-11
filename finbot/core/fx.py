import requests
import json
import shelve


API_URL = "https://api.exchangeratesapi.io"


def get_xccy_rate(domestic_ccy, foreign_ccy, date=None):
    def get_fx_rate_impl(home_ccy, foreign_ccy):
        if home_ccy == foreign_ccy:
            return 1.0
        date_str = date.strftime("%Y-%m-%d") if date else "latest"
        response = requests.get(
            f"{API_URL}/{date_str}?base={domestic_ccy.upper()}&symbols={foreign_ccy.upper()}")
        data = json.loads(response.content.decode())
        if "error" in data:
            raise RuntimeError(data["error"])
        return float(data["rates"][foreign_ccy.upper()])
    return get_fx_rate_impl(domestic_ccy, foreign_ccy)


def get_xccy_rate_cached(domestic_ccy, foreign_ccy, date=None):
    date_str = date.strftime("%Y-%m-%d") if date else "latest"
    cache_key = f"{date_str}/{domestic_ccy}/{foreign_ccy}"
    with shelve.open('/tmp/get_xccy_rate_cached') as db:
        if cache_key in db:
            return db[cache_key]
        rate = get_xccy_rate(domestic_ccy, foreign_ccy, date)
        if date is None:
            # no cache for spot
            return rate
        db[cache_key] = rate
        return rate
