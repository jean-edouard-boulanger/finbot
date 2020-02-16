from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from finbot import providers
from finbot.providers.support.selenium import SeleniumHelper
from finbot.providers.errors import AuthFailure
from functools import partial
import logging


BARCLAYCARD_URL = "https://www.barclaycard.co.uk/personal/customer"


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
        self.account = None

    def authenticate(self, credentials):
        self._do.get(BARCLAYCARD_URL)

        logging.info("getting logging form")
        login_button = self._do.wait_element(By.XPATH, "//a[@data-aem-js='loginButton']")
        self._do.click(login_button)

        # step 2: provide username

        logging.info(f"providing username {credentials.user_name}")
        username_input = self._do.wait_element(By.XPATH, "//input[@name='usernameAndID']")
        username_input.send_keys(credentials.user_name)
        self._do.find(By.XPATH, "//button[@type='submit']").click()

        self._do.assert_success(_get_password_input, _get_bad_id_error,
                                on_failure=partial(_report_auth_error, "providing username"))

        # step 3: provide passcode

        logging.info(f"providing passcode")
        passcode_input = self._do.wait_element(By.XPATH, "//input[@type='password']")
        passcode_input.send_keys(credentials.passcode)
        self._do.find(By.XPATH, "//button[@type='submit']").click()

        # step 4: provide partial memorable word

        logging.info(f"providing memorable word")

        input1 = self._do.wait_element(By.XPATH, "//input[@data-id='memorableWord-letter1']")
        input1_id = input1.get_attribute("id")

        input2 = self._do.wait_element(By.XPATH, "//input[@data-id='memorableWord-letter2']")
        input2_id = input2.get_attribute("id")

        letter1_label_id = f"{input1_id}-label"
        letter1_idx = int(self._do.wait_element(By.ID, letter1_label_id).text.strip()[0]) - 1

        letter2_label_id = f"{input2_id}-label"
        letter2_idx = int(self._do.wait_element(By.ID, letter2_label_id).text.strip()[0]) - 1

        input1.send_keys(credentials.memorable_word[letter1_idx])
        input2.send_keys(credentials.memorable_word[letter2_idx])
        self._do.find(By.XPATH, "//button[@type='submit']").click()

        self._do.assert_success(_is_logged_in, _get_login_error,
                                on_failure=partial(_report_auth_error, "providing credentials"))

        # step 5: collect account info
        account_area = self._do.wait_element(By.CSS_SELECTOR, "div.sitenav-select-account-link")
        account_name, account_id = account_area.text.strip().split("...")
        self.account = {
            "id": account_id,
            "name": account_name.strip(),
            "iso_currency": "GBP",
            "type": "credit"
        }

    def get_balances(self):
        balance_area = self._do.wait_element(By.CSS_SELECTOR, "div.current-balance")
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


def _report_auth_error(stage, error_message):
    raise AuthFailure(f"{error_message} (while {stage})")


def _is_logged_in(do: SeleniumHelper):
    account_area = do.find_maybe(By.CSS_SELECTOR, "div.sitenav-select-account-link")
    return account_area is not None


def _get_password_input(do: SeleniumHelper):
    return do.find_maybe(By.XPATH, "//input[@type='password']")


def _get_bad_id_error(do: SeleniumHelper):
    bad_id_error_area = do.find_maybe(By.ID, "usernameAndID-error")
    if bad_id_error_area:
        return bad_id_error_area.text.strip()


def _get_login_error(do: SeleniumHelper):
    form_error_area = do.find_maybe(By.CSS_SELECTOR, "form#login div.red.message")
    if form_error_area:
        return form_error_area.text.strip()
