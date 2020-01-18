from finbot import providers
from finbot.providers.support.selenium import any_of
from finbot.providers.errors import AuthFailure, Error
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from copy import deepcopy
import re
import time
from price_parser import Price


AUTH_URL = "https://global.americanexpress.com/login"


def _iter_accounts(browser):
    accounts_switcher_area = WebDriverWait(browser, 60).until(
        presence_of_element_located((By.CSS_SELECTOR, "section.axp-account-switcher")))
    accounts_switcher = accounts_switcher_area.find_element_by_tag_name("button")
    accounts_switcher.click()

    accounts_area = WebDriverWait(browser, 60).until(
        presence_of_element_located((By.ID, "accounts")))

    account_rows = accounts_area.find_elements_by_css_selector("section.account-row")
    for account_row in account_rows:
        account_name = account_row.text.strip()
        # TODO make this configurable?
        if "corporate" in account_name.lower():
            continue
        account_id = re.findall(r"\(-(\d+)\)", account_name)[0]
        yield {
            "account": {
                "id": account_id,
                "name": account_name,
                "iso_currency": "GBP"
            },
            "selenium": {
                "account_element_ref": account_row
            }
        }
    browser.execute_script("arguments[0].click();", accounts_switcher)


def _get_balance(balance_area):
    line_items = balance_area.find_elements_by_css_selector("div.line-item")
    for entry in line_items:
        header = entry.find_element_by_css_selector("div.header-container").text.lower()
        if "balance" in header:
            balance_str = entry.find_element_by_css_selector("div.data-value").text.strip()
            return Price.fromstring(balance_str)
    raise Error("unable to get balance")


class Credentials(object):
    def __init__(self, user_id, password):
        self._user_id = user_id
        self.password = password
    
    @property
    def user_id(self):
        return str(self._user_id)

    @staticmethod
    def init(data):
        return Credentials(data["user_id"], data["password"])


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = None

    def _switch_account(self, account_id):
        for entry in _iter_accounts(self.browser):
            if entry["account"]["id"] == account_id:
                entry["selenium"]["account_element_ref"].click()
                return WebDriverWait(self.browser, 60).until(
                    presence_of_element_located((By.CSS_SELECTOR, "section.balance-container")))
        raise Error(f"unable to switch to account {account_id}")

    def authenticate(self, credentials):
        browser = self.browser
        browser.get(AUTH_URL)
        cookies_mask = WebDriverWait(browser, 60).until(
            presence_of_element_located((By.ID, "euc_mask")))
        cookies_mask.click()

        browser.find_element_by_id("eliloUserID").send_keys(credentials.user_id)
        browser.find_element_by_id("eliloPassword").send_keys(credentials.password)
        browser.find_element_by_id("loginSubmit").click()

        self.accounts = {
            entry["account"]["id"]: deepcopy(entry["account"])
            for entry in _iter_accounts(browser)
        }

    def get_balances(self, account_ids=None):
        accounts = []
        for account_id, account in self.accounts.items():
            balance = _get_balance(self._switch_account(account_id))
            accounts.append({
                "account": deepcopy(account),
                "balance": balance.amount_float * -1.0
            })

        return {"accounts": accounts}

    def get_liabilities(self, account_ids=None):
        return {
            "accounts": [
                {
                    "account": deepcopy(entry["account"]),
                    "liabilities": [{
                        "name": "credit",
                        "type": "credit",
                        "value": entry["balance"]
                    }]
                }
                for entry in self.get_balances(account_ids)["accounts"]
            ]
        }
