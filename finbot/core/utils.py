from typing import TypeVar, Optional
from pytz import timezone
from datetime import datetime
import logging.config
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


def pretty_dump(data) -> str:
    def fallback(unhandled_data):
        return f"<not serializable {type(unhandled_data)} {unhandled_data}>"

    return json.dumps(serialize(data), indent=4, default=fallback)


def now_utc() -> datetime:
    return datetime.now(timezone("UTC"))


def in_range(value, from_value, to_value) -> bool:
    if from_value and value < from_value:
        return False
    if to_value and value > to_value:
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


def configure_logging():
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "%(asctime)s"
                    " (%(threadName)s)"
                    " [%(levelname)s]"
                    " %(message)s"
                    " (%(filename)s:%(lineno)d)",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                }
            },
            "root": {"level": "INFO", "handlers": ["wsgi"]},
        }
    )


T = TypeVar("T")


def unwrap_optional(val: Optional[T]) -> T:
    assert val is not None
    return val
