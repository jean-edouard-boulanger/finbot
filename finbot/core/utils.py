import functools
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Iterator, Optional, Type, TypeVar

import stackprinter
from pytz import timezone


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


def fully_qualified_type_name(obj: Any) -> str:
    t = type(obj)
    return f"{t.__module__}.{t.__qualname__}"


T = TypeVar("T")


def unwrap_optional(val: Optional[T]) -> T:
    assert val is not None
    return val


@dataclass
class StackPrinterSettings:
    show_vals: Optional[str] = field(default_factory=lambda: "all")
    style: str = field(default_factory=lambda: "plaintext")

    def as_kwargs(self) -> dict[str, Any]:
        return asdict(self)

    def clone(self) -> "StackPrinterSettings":
        return StackPrinterSettings(**asdict(self))


STACK_PRINTER_SETTINGS = StackPrinterSettings()


def configure_stack_printer(**kwargs: Any) -> None:
    global STACK_PRINTER_SETTINGS
    STACK_PRINTER_SETTINGS = StackPrinterSettings(**kwargs)


def _get_stack_printer_settings() -> StackPrinterSettings:
    global STACK_PRINTER_SETTINGS
    return STACK_PRINTER_SETTINGS


@contextmanager
def scoped_stack_printer_configuration(**kwargs: Any) -> Iterator[None]:
    old_settings = _get_stack_printer_settings().clone()
    try:
        configure_stack_printer(**kwargs)
        yield
    finally:
        configure_stack_printer(**old_settings.as_kwargs())


def format_stack(thing: Optional[Exception] = None, **kwargs: Any) -> str:
    sp_settings = _get_stack_printer_settings()
    output: str = stackprinter.format(thing, **{**sp_settings.as_kwargs(), **kwargs})
    return output


def raise_(ex: Exception) -> None:
    raise ex
