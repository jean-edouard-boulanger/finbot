from finbot.providers.support.selenium import DefaultBrowserFactory, SeleniumHelper
from datetime import datetime


class Base(object):
    def __init__(self, **kwargs):
        pass

    def authenticate(self, credentials):
        """ Authenticate user with provided credentials. Should persist any
        information needed to perform further operations (get balances,
        get assets, get liabilities)

        :raises AuthFailure: should be raised if authentication failed
        """
        pass

    def get_balances(self):
        """
        """
        return {"accounts": []}

    def get_assets(self):
        """
        """
        return {"accounts": []}

    def get_liabilities(self):
        """
        """
        return {"accounts": []}

    def get_transactions(self, from_date: datetime, to_date: datetime):
        """
        """
        return {"accounts": []}

    def close(self):
        """ Implement to release any used resource at the end of the session
        """
        pass


class SeleniumBased(Base):
    def __init__(self, browser_factory=None, **kwargs):
        super().__init__(**kwargs)
        browser_factory = browser_factory or DefaultBrowserFactory()
        self.browser = browser_factory()
        self._do = SeleniumHelper(self.browser)

    def close(self):
        self.browser.quit()
