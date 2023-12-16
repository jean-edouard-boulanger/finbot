import time
from abc import ABC
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Generator, Self

from playwright.sync_api import (
    Browser,
    Error,
    Locator,
    Page,
    Playwright,
    sync_playwright,
)

from finbot.providers.base import ProviderBase


def _get_default_chrome_options(window_size: tuple[int, int]) -> list[str]:
    return [
        "--disable-dev-shm-usage",
        "--temp-profile",
        "--incognito",
        "--disable-gpu",
        f"--window-size={window_size[0]},{window_size[1]}",
        "--window-position=0,0",
    ]


class BrowserLauncher(object):
    def __init__(self, playwright: Playwright) -> None:
        self._playwright = playwright
        self._browser: Browser | None = None

    def __enter__(self) -> "BrowserLauncher":
        window_size = (1920, 1080)
        self._browser = self._playwright.chromium.launch(
            headless=False,
            args=_get_default_chrome_options(window_size),
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        assert self._browser
        self._browser.close()

    @property
    def browser(self) -> Browser:
        assert self._browser
        return self._browser


class PlaywrightHelperError(Exception):
    pass


class TimedOutWaitingForConditions(PlaywrightHelperError):
    pass


@dataclass(frozen=True)
class Condition:
    predicate: Callable[[], Any]
    when_fulfilled: Callable[[Any], None] | None = None


class ConditionGuard(object):
    default_timeout = timedelta(seconds=30)
    default_poll_interval = timedelta(seconds=0.05)

    def __init__(
        self,
        *conditions: Condition,
        poll_interval: timedelta | None = None,
        timeout: timedelta | None = None,
    ):
        self._conditions = conditions
        self._poll_interval = poll_interval or self.default_poll_interval
        self._timeout = timeout or self.default_timeout

    def _timed_loop(self) -> Generator[None, None, None]:
        timeout_at = (datetime.now() + self._timeout) if self._timeout else None
        while True:
            if timeout_at and datetime.now() >= timeout_at:
                raise TimedOutWaitingForConditions(
                    f"timed out waiting for {len(self._conditions)} conditions"
                    f" after {self._timeout.total_seconds()} seconds"
                )
            yield
            time.sleep(self._poll_interval.total_seconds())

    def wait_all(self) -> tuple[Any, ...]:
        when_fulfilled_callbacks = [cond.when_fulfilled for cond in self._conditions]
        for _ in self._timed_loop():
            all_vals = tuple(cond.predicate() for cond in self._conditions)
            all_true = True
            for index, val in enumerate(all_vals):
                if bool(val):
                    when_fulfilled = when_fulfilled_callbacks[index]
                    when_fulfilled and when_fulfilled(val)
                    when_fulfilled_callbacks[index] = None
                else:
                    all_true = False
            if all_true:
                return all_vals
        return tuple()

    def wait_any(self) -> tuple[int, Any]:
        for _ in self._timed_loop():
            for index, cond in enumerate(self._conditions):
                if val := cond.predicate():
                    cond.when_fulfilled and cond.when_fulfilled(val)
                    return index, val
        return -1, None

    def wait(self) -> Any:
        assert len(self._conditions) == 1
        return self.wait_all()[0]


class PlaywrightProviderBase(ProviderBase, ABC):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._launcher: BrowserLauncher | None = None
        self._stack: ExitStack | None = None
        self._page: Page | None = None

    def __enter__(self) -> Self:
        with ExitStack() as stack:
            playwright: Playwright = stack.enter_context(sync_playwright())
            self._launcher = stack.enter_context(BrowserLauncher(playwright))
            self._page = self.browser.new_page()
            self._stack = stack.pop_all()
        return self

    @property
    def browser(self) -> Browser:
        assert self._launcher
        return self._launcher.browser

    @property
    def page(self) -> Page:
        assert self._page
        return self._page

    def get_element_or_none(self, selector: str) -> Locator | None:
        try:
            el = self.page.locator(selector)
            if el.is_visible():
                return el
            return None
        except Error:
            return None

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        assert self._stack
        self._stack.__exit__(exc_type, exc_val, exc_tb)
