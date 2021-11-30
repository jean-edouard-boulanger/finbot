from typing import Optional, Callable, Any
from functools import wraps
from os.path import expanduser

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement

from undetected_chromedriver.v2 import Chrome, ChromeOptions
import filelock


class DefaultBrowserFactory(object):
    def __init__(self, headless: bool = True, developer_tools: bool = False) -> None:
        self.headless = headless
        self.developer_tools = developer_tools

    def __call__(self) -> Chrome:
        options = ChromeOptions()
        options.add_argument("--no-first-run")
        options.add_argument("--password-store=basic")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        if self.developer_tools:
            options.add_argument("--auto-open-devtools-for-tabs")

        # Prevents multiple processes from patching the chromedriver executable at once
        # Review: possibly over-engineered
        with filelock.FileLock(expanduser("~/.finbot.undetected_chromedriver.lock")):
            return Chrome(
                options=options, executable_path="/usr/bin/chromedriver", headless=True
            )


def _safe_cond(cond: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(cond)
    def impl(*args: Any, **kwargs: Any) -> Any:
        try:
            return cond(*args, **kwargs)
        except Exception:
            return None

    return impl


class any_of(object):
    def __init__(self, *args: Any) -> None:
        self.conds = [_safe_cond(cond) for cond in args]

    def __call__(self, driver: WebDriver) -> bool:
        return any(cond(driver) for cond in self.conds)


class SeleniumHelper(object):
    def __init__(self, browser: WebDriver):
        self.browser = browser

    @property
    def current_url(self) -> Any:
        return self.browser.current_url

    @property
    def cookies(self) -> dict[str, str]:
        return {
            str(cookie["name"]): str(cookie["value"])
            for cookie in self.browser.get_cookies()
        }

    def get(self, url: str) -> None:
        self.browser.get(url)

    def wait(self, timeout: int = 60) -> WebDriverWait:
        return WebDriverWait(self.browser, timeout)

    def wait_element(self, by: str, selector: str, timeout: int = 60) -> WebElement:
        return self.wait(timeout).until(presence_of_element_located((by, selector)))

    def wait_cond(self, cond: Callable[..., Optional[Any]], timeout: int = 60) -> Any:
        return self.wait(timeout).until(cond)

    def find(self, by: str, selector: str) -> WebElement:
        return self.browser.find_element(by, selector)

    def find_many(self, by: str, selector: str) -> list[WebElement]:
        results: list[WebElement] = self.browser.find_elements(by, selector)
        return results

    def find_maybe(self, by: str, selector: str) -> Optional[WebElement]:
        all_elements = self.find_many(by, selector)
        if not all_elements:
            return None
        return all_elements[0]

    def execute_script(self, *args: Any, **kwargs: Any) -> Any:
        return self.browser.execute_script(*args, **kwargs)

    def click(self, element: WebElement) -> None:
        self.execute_script("arguments[0].click();", element)

    def dump_html(self, element: WebElement) -> str:
        result: str = element.get_attribute("innerHTML")
        return result

    def save_screenshot(self, name: str) -> Any:
        return self.browser.save_screenshot(name)

    def assert_success(
        self,
        success_predicate: Callable[..., Optional[Any]],
        failure_predicate: Callable[..., Optional[Any]],
        on_failure: Optional[Callable[..., Any]] = None,
        timeout: int = 60,
    ) -> Any:
        on_failure = on_failure or (lambda _: None)
        self.wait_cond(
            any_of(
                lambda _: success_predicate(self), lambda _: failure_predicate(self)
            ),
            timeout=timeout,
        )
        failure_data = failure_predicate(self)
        if failure_data:
            return on_failure(failure_data)
