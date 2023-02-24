import time
from typing import Any, Callable, Generator
from contextlib import ExitStack
from datetime import datetime, timedelta
from dataclasses import dataclass

from playwright.sync_api import sync_playwright, Playwright, Browser, Page

from finbot import providers


@dataclass
class BrowserSettings:
    enable_virtual_display: bool = True


def _get_default_chrome_options(window_size: tuple[int, int]) -> list[str]:
    return [
        "--disable-dev-shm-usage",
        "--kiosk",
        "--temp-profile",
        "--incognito",
        "--disable-gpu",
        f"--window-size={window_size[0]},{window_size[1]}",
        "--window-position=0,0",
        "--disable-extensions",
        "--disable-3d-apis",
        "--disable-plugins",
        "--js-flags=--noexpose_wasm",
        "--no-experiments",
    ]


class BrowserLauncher(object):
    def __init__(self, playwright: Playwright, settings: BrowserSettings) -> None:
        self._playwright = playwright
        self._browser: Browser | None = None
        self._settings = settings

    def __enter__(self) -> "BrowserLauncher":
        window_size = (1920, 1080)
        self._browser = self._playwright.chromium.launch(
            headless=False, args=_get_default_chrome_options(window_size)
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


class TimedOut(PlaywrightHelperError):
    pass


class Waiter(object):
    def __init__(
        self, conditions: list[Callable[[], bool]], timeout: timedelta | None = None
    ):
        self._conds = conditions
        self._timeout = timeout or timedelta(seconds=30)

    def _timed_loop(self) -> Generator[None, None, None]:
        timeout_at = (datetime.now() + self._timeout) if self._timeout else None
        while True:
            if timeout_at and datetime.now() >= timeout_at:
                raise TimedOut(
                    f"timed out after {self._timeout.total_seconds()} seconds"
                )
            yield
            time.sleep(0.05)

    def wait_all(self) -> list[Any]:
        for _ in self._timed_loop():
            all_items = [cond() for cond in self._conds]
            if all(all_items):
                return all_items
        return []

    def wait_any(self) -> int:
        for _ in self._timed_loop():
            for index, cond in enumerate(self._conds):
                if cond():
                    return index
        return -1


class PlaywrightHelper(object):
    @staticmethod
    def wait(condition: Callable[[], Any], timeout: timedelta | None = None) -> Any:
        return Waiter(conditions=[condition], timeout=timeout).wait_all()[0]


class PlaywrightBased(providers.Base, PlaywrightHelper):
    def __init__(
        self, playwright_settings: BrowserSettings | None = None, **kwargs: Any
    ):
        super().__init__(**kwargs)
        self._settings = playwright_settings or BrowserSettings()
        self._launcher: BrowserLauncher | None = None
        self._stack: ExitStack | None = None
        self._page: Page | None = None

    def __enter__(self) -> "PlaywrightBased":
        with ExitStack() as stack:
            playwright: Playwright = stack.enter_context(sync_playwright())
            self._launcher = stack.enter_context(
                BrowserLauncher(playwright, self._settings)
            )
            self._page = self.browser.new_page()
            self._stack = stack.pop_all()
        self.initialize()
        return self

    @property
    def browser(self) -> Browser:
        assert self._launcher
        return self._launcher.browser

    @property
    def page(self) -> Page:
        assert self._page
        return self._page

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        assert self._stack
        self._stack.__exit__(exc_type, exc_val, exc_tb)
