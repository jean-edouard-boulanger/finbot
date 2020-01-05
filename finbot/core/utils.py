from pytz import timezone
from datetime import datetime
import decimal
import json


def pretty_dump(data):
    def fallback(data):
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, decimal.Decimal):
            return float(data)
        return f"<not serializable {type(data)} {data}>"
    return json.dumps(data, indent=4, default=fallback)


def serialize(data):
    if isinstance(data, decimal.Decimal):
        return float(data)
    if isinstance(data, datetime):
        return data.isoformat()
    if isinstance(data, dict):
        return {serialize(k): serialize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [serialize(v) for v in data]
    return data


def now_utc():
    return datetime.now(timezone('UTC'))
