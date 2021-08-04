from finbot import providers
from finbot.providers.support.selenium import DefaultBrowserFactory, SeleniumHelper

from selenium.webdriver.remote.webdriver import WebDriver

from typing import Callable, Optional


class SeleniumBased(providers.Base):
    def __init__(self, browser_factory: Optional[Callable[[], WebDriver]] = None):
        super().__init__()
        browser_factory = browser_factory or DefaultBrowserFactory()
        self.browser = browser_factory()
        self._do = SeleniumHelper(self.browser)

    @property
    def user_agent(self) -> str:
        result: str = self._do.execute_script("return navigator.userAgent")
        return result

    def close(self) -> None:
        self.browser.quit()
