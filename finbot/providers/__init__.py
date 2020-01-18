from finbot.providers.support.selenium import DefaultBrowserFactory


class Base(object):
    def __init__(self, **kwargs):
        pass

    def authenticate(self, credentials):
        """ Authenticate user with provided credentials. Should persist any
        informations needed to perform further operations (get balances, 
        get assets, get liabilities)

        :raises AuthFailure: should be raised if authentication failed
        """
        pass

    def get_balances(self, account_ids=None):
        """
        """
        return {"accounts": []}

    def get_assets(self, account_ids=None):
        """
        """
        return {"accounts": []}

    def get_liabilities(self, account_ids=None):
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

    def close(self):
        self.browser.quit()
