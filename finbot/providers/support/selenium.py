from typing import List, Optional, Dict
from functools import wraps
from os.path import expanduser

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement

import filelock


class DefaultBrowserFactory(object):
    def __init__(self, headless=True, developer_tools=False):
        self.headless = headless
        self.developer_tools = developer_tools

    def __call__(self):
        from undetected_chromedriver.v2 import Chrome, ChromeOptions

        options = ChromeOptions()
        options.add_argument("--no-first-run")
        options.add_argument("--password-store=basic")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        if self.developer_tools:
            options.add_argument("--auto-open-devtools-for-tabs")
        options.headless = self.headless

        # Prevents multiple processes from patching the chromedriver executable at once
        # Review: possibly over-engineered
        with filelock.FileLock(expanduser("~/.finbot.undetected_chromedriver.lock")):
            return Chrome(options=options)


def _safe_cond(cond):
    @wraps(cond)
    def impl(*args, **kwargs):
        try:
            return cond(*args, **kwargs)
        except Exception:
            return None

    return impl


class any_of(object):
    def __init__(self, *args):
        self.conds = [_safe_cond(cond) for cond in args]

    def __call__(self, driver):
        return any(cond(driver) for cond in self.conds)


class all_of(object):
    def __init__(self, *args):
        self.conds = [_safe_cond(cond) for cond in args]

    def __call__(self, driver):
        return all(cond(driver) for cond in self.conds)


class negate(object):
    def __init__(self, cond):
        self.cond = _safe_cond(cond)

    def __call__(self, driver):
        return not (self.cond(driver))


class SeleniumHelper(object):
    def __init__(self, browser: WebDriver):
        self.browser = browser

    @property
    def current_url(self):
        return self.browser.current_url

    @property
    def cookies(self) -> Dict[str, str]:
        return {
            str(cookie["name"]): str(cookie["value"])
            for cookie in self.browser.get_cookies()
        }

    def get(self, url) -> None:
        self.browser.get(url)

    def wait(self, timeout=60):
        return WebDriverWait(self.browser, timeout)

    def wait_element(self, by, selector, timeout=60) -> WebElement:
        return self.wait(timeout).until(presence_of_element_located((by, selector)))

    def wait_cond(self, cond, timeout=60):
        return self.wait(timeout).until(cond)

    def find(self, by, selector) -> WebElement:
        return self.browser.find_element(by, selector)

    def find_many(self, by, selector) -> List[WebElement]:
        return self.browser.find_elements(by, selector)

    def find_maybe(self, by, selector) -> Optional[WebElement]:
        all_elements = self.find_many(by, selector)
        if not all_elements:
            return None
        return all_elements[0]

    def execute_script(self, *args, **kwargs):
        return self.browser.execute_script(*args, **kwargs)

    def click(self, element: WebElement):
        self.execute_script("arguments[0].click();", element)

    def dump_html(self, element: WebElement):
        return element.get_attribute("innerHTML")

    def save_screenshot(self, name: str):
        return self.browser.save_screenshot(name)

    def assert_success(
        self, success_predicate, failure_predicate, on_failure=None, timeout=60
    ):
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
