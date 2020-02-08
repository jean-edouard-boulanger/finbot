from selenium.webdriver.common.by import By
from finbot import providers
from finbot.core.utils import swallow_exc
from finbot.providers.support.selenium import any_of, get_cookies
from selenium.common.exceptions import StaleElementReferenceException
from finbot.providers.errors import AuthFailure, Error
import requests
import logging
import csv
import io


AUTH_URL = "https://www.lendingworks.co.uk/sign-in"
DASHBOARD_URL = "https://www.lendingworks.co.uk/lending-centre/{ns}"
LOANS_EXPORT_URL = "https://www.lendingworks.co.uk/lending-centre/{ns}/my-loans/export"


def _is_logged_in(browser_helper: providers.SeleniumHelper):
    return len(browser.find_elements_by_css_selector("body.logged-in")) > 0


@swallow_exc(StaleElementReferenceException)
def _get_login_error(browser_helper: providers.SeleniumHelper):
    error_element = browser_helper.find_maybe(By.CSS_SELECTOR, "div.alert-block")
    if error_element and error_element.is_displayed():
        return error_element.text.strip()


class Credentials(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    @property
    def user_id(self):
        return self.username

    @staticmethod
    def init(data):
        return Credentials(data["username"], data["password"])


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._accounts = {}

    def _get_loans(self, account_type):
        def _chunk_outstanding(row):
            return float(row["Chunk Amount"]) - float(row["Chunk Capital Repaid"])
        cookies = get_cookies(self.browser)
        loans_endpoint = LOANS_EXPORT_URL.format(ns=account_type)
        response = requests.get(loans_endpoint, cookies=cookies)
        csv_data = response.content.decode()
        all_data = list(csv.DictReader(io.StringIO(csv_data)))
        return [
            {
                "name": f"{row['Loan ID']}-{row['Chunk ID']}",
                "type": "loan",
                "value": _chunk_outstanding(row),
            }
            for row in all_data
        ]

    def _get_account_data(self, account_key):
        def do_get_account_data(_):
            all_data = self.browser.execute_script("return window.data.appData;")
            account_data = all_data[account_type]
            if "total_account_balance" in account_data:
                return account_data
            return None
        account_type, _ = account_key
        if not self._accounts[account_key]:
            account_url = DASHBOARD_URL.format(ns=account_type)
            self._do.get(account_url)
            self._accounts[account_key] = {
                "summary": self._do.wait_cond(do_get_account_data),
                "loans": self._get_loans(account_type)
            }
        return self._accounts[account_key]

    def _iter_accounts(self):
        for account_key in self._accounts:
            account_type, account_name = account_key
            data = self._get_account_data(account_key)
            yield {
                "account": {
                    "id": account_type,
                    "name": account_name,
                    "iso_currency": "GBP"
                },
                "balance": data["summary"]["total_account_balance"],
                "assets": [
                    {
                        "name": "offers", 
                        "type": "currency", 
                        "value": data["summary"]["total_offers"]
                    },
                    {
                        "name": "wallet",
                        "type": "currency",
                        "value": data["summary"]["wallet_total"]
                    }
                ] + data["loans"]
            }

    def authenticate(self, credentials):
        browser = self.browser
        browser.get(AUTH_URL)

        # 1. Enter credentials and validate

        login_block = self._do.wait_element(By.CSS_SELECTOR, "div.m-lw-login-block")
        username_input, password_input, *_ = login_block.find_elements_by_tag_name("input")
        username_input.send_keys(credentials.username)
        password_input.send_keys(credentials.password)
        submit_button = self._do.find(By.CSS_SELECTOR, "button.form-submit")
        submit_button.click()

        # 2. Wait logged-in or error

        self._do.wait_cond(any_of(
            lambda _: _is_logged_in(self._do), 
            lambda _: _get_error(self._do)))

        error_message = _get_login_error(self._do)
        if error_message:
            raise AuthFailure(error_message)

        # 3. Register available accounts types

        self._do.wait_element(By.CLASS_NAME, "onboarding-heading")
        classic_btn, isa_btn = self._do.find_many(By.CSS_SELECTOR, "div.btn")

        if "view" in classic_btn.text.lower():
            self._accounts[("classic", "Classic account")] = None
        if "view" in isa_btn.text.lower():
            self._accounts[("ifisa", "ISA account")] = None

    def get_balances(self):
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "balance": entry["balance"]
                }
                for entry in self._iter_accounts()
            ]
        }

    def get_assets(self):
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "assets": entry["assets"]
                }
                for entry in self._iter_accounts()
            ]
        }
