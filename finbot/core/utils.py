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


def now_utc():
    return datetime.now(timezone('UTC'))
