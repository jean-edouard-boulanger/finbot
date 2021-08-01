from finbot import providers
from finbot.providers.support.selenium import DefaultBrowserFactory, SeleniumHelper


class SeleniumBased(providers.Base):
    def __init__(self, browser_factory=None, **kwargs):
        super().__init__(**kwargs)
        browser_factory = browser_factory or DefaultBrowserFactory()
        self.browser = browser_factory()
        self._do = SeleniumHelper(self.browser)

    @property
    def user_agent(self) -> str:
        return self._do.execute_script("return navigator.userAgent")

    def close(self):
        self.browser.quit()
