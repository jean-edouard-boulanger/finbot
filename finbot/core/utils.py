import functools
from datetime import datetime
from typing import Any, Callable, Optional, Type, TypeVar

from pytz import timezone


def now_utc() -> datetime:
    return datetime.now(timezone("UTC"))


def swallow_exc(*exc_types: Type[BaseException], default: Optional[Any] = None) -> Callable[..., Any]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def impl(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except exc_types:
                return default

        return impl

    return decorator


def fully_qualified_type_name(obj: Any) -> str:
    t = type(obj)
    return f"{t.__module__}.{t.__qualname__}"


T = TypeVar("T")


def some(val: T | None) -> T:
    assert val is not None
    return val


def raise_(ex: Exception) -> None:
    raise ex


def float_or_none(value: int | float | str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None
