from typing import List, Optional, Dict
from functools import wraps
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement


class DefaultBrowserFactory(object):
    def __init__(self, headless=True, developer_tools=False):
        self.headless = headless
        self.developer_tools = developer_tools

    def __call__(self):
        from selenium.webdriver import Chrome
        from selenium.webdriver.chrome.options import Options
        opts = Options()
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--no-sandbox")
        if self.developer_tools:
            opts.add_argument("--auto-open-devtools-for-tabs")
        opts.headless = self.headless
        driver = Chrome(options=opts)
        return driver


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
        return not(self.cond(driver))


class SeleniumHelper(object):
    def __init__(self, browser):
        self.browser = browser

    def get(self, url):
        self.browser.get(url)

    def wait(self, timeout=60):
        return WebDriverWait(self.browser, timeout)

    def wait_element(self, by, selector, timeout=60) -> WebElement:
        return self.wait(timeout).until(
            presence_of_element_located((by, selector)))

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

    def click(self, element):
        self.execute_script("arguments[0].click();", element)

    def get_cookies(self) -> Dict[str, str]:
        return {
            cookie["name"]: cookie["value"] 
            for cookie in self.browser.get_cookies()
        }
