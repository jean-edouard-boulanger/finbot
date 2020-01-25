from finbot.providers.support.selenium import DefaultBrowserFactory
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait


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

    def get_transactions(self, from_date, to_date):
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

    def _wait_element(self, by, selector, timeout=60):
        return WebDriverWait(self.browser, timeout).until(
            presence_of_element_located((by, selector)))

    def _wait(self, timeout=60):
        return WebDriverWait(self.browser, timeout)

    def _find(self, by, selector):
        return self.browser.find_element(by, selector)

    def _find_many(self, by, selector):
        return self.browser.find_elements(by, selector)

    def _find_maybe(self, by, selector):
        all_elements = self._find_many(by, selector)
        if not all_elements:
            return None
        return all_elements[0]

    def _click_js(self, element):
        self.browser.execute_script("arguments[0].click();", element)

    def close(self):
        self.browser.quit()
