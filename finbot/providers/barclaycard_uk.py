from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from finbot import providers
from finbot.providers.support.selenium import any_of
from finbot.providers.errors import AuthFailure
import re
import time
import logging


BARCLAYCARD_URL = "https://www.barclaycard.co.uk/personal/customer"


def _get_login_error(browser):
    form_error_area = browser.find_elements_by_xpath("//div[contains(@class, 'FormErrorWell')]")
    if form_error_area:
        return form_error_area[0].find_element_by_tag_name("strong").text.strip()
    return None


class Credentials(object):
    def __init__(self, user_name, passcode, memorable_word):
        self.user_name = user_name
        self.passcode = passcode
        self.memorable_word = memorable_word

    @property
    def user_id(self):
        return str(self.user_name)

    @staticmethod
    def init(data):
        return Credentials(
            data["username"],
            data["passcode"],
            data["memorable_word"])


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = None

    def authenticate(self, credentials):
        browser = self.browser
        browser.get(BARCLAYCARD_URL)

        logging.info("getting logging form")
        login_button = self._wait_element(By.XPATH, "//a[@data-aem-js='loginButton']")
        browser.execute_script("arguments[0].click();", login_button)

        # step 2: provide username
        logging.info(f"providing username {credentials.user_name}")
        username_input = self._wait_element(By.XPATH, "//input[@name='usernameAndID']")
        username_input.send_keys(credentials.user_name)
        browser.find_element_by_xpath("//button[@type='submit']").click()

        # step 3: provide passcode
        logging.info(f"providing passcode")
        passcode_input = self._wait_element(By.XPATH, "//input[@type='password']")
        passcode_input.send_keys(credentials.passcode)
        browser.find_element_by_xpath("//button[@type='submit']").click()

        # step 4: provide partial memorable word
        logging.info(f"providing memorable word")
        input1 = self._wait_element(By.ID, "memorableWord_0_letter1")
        input2 = self._wait_element(By.ID, "memorableWord_1_letter2")
        letter1_idx = int(self._wait_element(By.ID, "memorableWord_0_letter1-label").text.strip()[0]) - 1
        letter2_idx = int(self._wait_element(By.ID, "memorableWord_1_letter2-label").text.strip()[0]) - 1
        input1.send_keys(credentials.memorable_word[letter1_idx])
        input2.send_keys(credentials.memorable_word[letter2_idx])
        browser.find_element_by_xpath("//button[@type='submit']").click()

        self._wait().until(any_of(
            presence_of_element_located((By.CSS_SELECTOR, "div.sitenav-select-account-link")),
            _get_login_error
        ))

        login_error = _get_login_error(browser)
        if login_error:
            raise AuthFailure(login_error)

        # step 5: collect account info
        account_area = self._wait_element(By.CSS_SELECTOR, "div.sitenav-select-account-link")
        account_name, account_id = account_area.text.strip().split("...")
        self.account = {
            "id": account_id,
            "name": account_name.strip(),
            "iso_currency": "GBP"
        }

    def get_balances(self):
        browser = self.browser
        balance_area = self._wait_element(By.CSS_SELECTOR, "div.current-balance")
        balance_amount_str = balance_area.find_element_by_css_selector("span.value").text.strip()
        balance_amount = Price.fromstring(balance_amount_str)
        return {
            "accounts": [
                {
                    "account": deepcopy(self.account),
                    "balance": balance_amount.amount_float * -1.0
                }
            ]
        }

    def get_liabilities(self):
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "liabilities": [{
                        "name": "credit",
                        "type": "credit",
                        "value": entry["balance"]
                    }]
                }
                for entry in self.get_balances()["accounts"]
            ]
        }
