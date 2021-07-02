from typing import TypeVar, Optional, Any, Union, Callable, Type
from pytz import timezone
from datetime import datetime
import logging.config
import functools
import decimal
import json


def serialize(data: Any) -> Any:
    def serialize_key(key: Any) -> Optional[Union[str, int, float, bool]]:
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
    if isinstance(data, (list, set, tuple)):
        return [serialize(v) for v in data]
    return data


def pretty_dump(data: Any) -> str:
    def fallback(unhandled_data: Any) -> str:
        return f"<not serializable {type(unhandled_data)} {unhandled_data}>"

    return json.dumps(serialize(data), indent=4, default=fallback)


def now_utc() -> datetime:
    return datetime.now(timezone("UTC"))


def swallow_exc(
    *exc_types: Type[BaseException], default: Optional[Any] = None
) -> Callable[..., Any]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def impl(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except exc_types:
                return default

        return impl

    return decorator


def configure_logging() -> None:
    logging.config.dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '%(asctime)s (%(threadName)s) [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        }},
        'root': {
            'level': "INFO",
            'handlers': ['wsgi']
        }
    })


T = TypeVar("T")


def unwrap_optional(val: Optional[T]) -> T:
    assert val is not None
    return val
