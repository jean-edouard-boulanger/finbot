from abc import ABC
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Awaitable, Callable, Self

from playwright.async_api import (
    Browser,
    Error,
    Locator,
    Page,
    Playwright,
    async_playwright,
)

from finbot.core.async_ import maybe_awaitable
from finbot.providers.base import ProviderBase

HEADLESS_SETTING = "headless_playwright"


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
    def __init__(self, playwright: Playwright, headless: bool) -> None:
        self._playwright = playwright
        self._browser: Browser | None = None
        self._headless = headless

    async def __aenter__(self) -> "BrowserLauncher":
        window_size = (1920, 1080)
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=_get_default_chrome_options(window_size),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        assert self._browser
        await self._browser.close()

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
    predicate: Callable[[], Awaitable[Any] | Any]
    when_fulfilled: Callable[[Any], Awaitable[None] | None] | None = None


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

    async def _timer(self, page: Page) -> AsyncGenerator[None]:
        timeout_at = (datetime.now() + self._timeout) if self._timeout else None
        while True:
            if timeout_at and datetime.now() >= timeout_at:
                raise TimedOutWaitingForConditions(
                    f"timed out waiting for {len(self._conditions)} conditions"
                    f" after {self._timeout.total_seconds()} seconds"
                )
            yield
            await page.wait_for_timeout(self._poll_interval.total_seconds() * 1000.0)

    async def wait_all(self, page: Page) -> tuple[Any, ...]:
        when_fulfilled_callbacks = [cond.when_fulfilled for cond in self._conditions]
        async for _ in self._timer(page):
            vals_lst: list[Any] = []
            for cond in self._conditions:
                vals_lst.append(await maybe_awaitable(cond.predicate()))
            all_vals = tuple(vals_lst)
            all_true = True
            for index, val in enumerate(all_vals):
                if bool(val):
                    if when_fulfilled := when_fulfilled_callbacks[index]:
                        await maybe_awaitable(when_fulfilled(val))
                    when_fulfilled_callbacks[index] = None
                else:
                    all_true = False
            if all_true:
                return all_vals
        return tuple()

    async def wait_any(self, page: Page) -> tuple[int, Any]:
        async for _ in self._timer(page):
            for index, cond in enumerate(self._conditions):
                if val := (await cond.predicate()):
                    if cond.when_fulfilled:
                        cond.when_fulfilled(val)
                    return index, val
        return -1, None

    async def wait(self, page: Page) -> Any:
        assert len(self._conditions) == 1
        return (await self.wait_all(page))[0]


class PlaywrightProviderBase(ProviderBase, ABC):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._launcher: BrowserLauncher | None = None
        self._stack: AsyncExitStack | None = None
        self._page: Page | None = None
        self._headless: bool = kwargs.pop(HEADLESS_SETTING, True)

    async def __aenter__(self) -> Self:
        async with AsyncExitStack() as stack:
            playwright: Playwright = await stack.enter_async_context(async_playwright())
            self._launcher = await stack.enter_async_context(BrowserLauncher(playwright, self._headless))
            self._page = await self.browser.new_page()
            self._stack = stack.pop_all()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        assert self._stack
        await self._stack.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def browser(self) -> Browser:
        assert self._launcher
        return self._launcher.browser

    @property
    def page(self) -> Page:
        assert self._page
        return self._page

    async def get_element_or_none(self, selector: str) -> Locator | None:
        try:
            el = self.page.locator(selector)
            if await el.is_visible():
                return el
            return None
        except Error:
            return None
