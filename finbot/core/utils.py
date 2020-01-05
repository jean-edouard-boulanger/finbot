from pytz import timezone
from datetime import datetime
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
