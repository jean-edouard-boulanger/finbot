from pytz import timezone
from datetime import datetime
import functools
import decimal
import json


def serialize(data):
    def serialize_key(key):
        if key is None:
            return key
        if not isinstance(key, (str, int, float, bool)):
            return str(key)
        return key
    if hasattr(data, "serialize"):
        return serialize(data.serialize())
    if isinstance(data, decimal.Decimal):
        return float(data)
    if isinstance(data, datetime):
        return data.isoformat()
    if isinstance(data, dict):
        return {serialize_key(k): serialize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [serialize(v) for v in data]
    return data


def pretty_dump(data):
    def fallback(unhandled_data):
        return f"<not serializable {type(unhandled_data)} {unhandled_data}>"
    return json.dumps(serialize(data), indent=4, default=fallback)


def now_utc():
    return datetime.now(timezone('UTC'))


def date_in_range(date, from_date, to_date):
    if from_date and date < from_date:
        return False
    if to_date and date > to_date:
        return False
    return True


def swallow_exc(*exc_types, default=None):
    def decorator(func):
        @functools.wraps(func)
        def impl(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exc_types:
                return default
        return impl
    return decorator
