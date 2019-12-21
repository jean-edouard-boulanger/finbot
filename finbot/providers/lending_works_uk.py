from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import (
    staleness_of, 
    presence_of_element_located
)
from selenium.common.exceptions import StaleElementReferenceException
from finbot import providers
from finbot.providers.support.selenium import (
    DefaultBrowserFactory, any_of, all_of, negate, dump_html, get_cookies
)
from finbot.providers.errors import AuthFailure
from copy import deepcopy
import requests
import logging
import csv
import io


AUTH_URL = "https://www.lendingworks.co.uk/sign-in"
CLASSIC_URL = "https://www.lendingworks.co.uk/lending-centre/classic"
LOANS_EXPORT_URL = "https://www.lendingworks.co.uk/lending-centre/classic/my-loans/export"


def json_dumps(data):
    import json
    return json.dumps(data, indent=4)


def is_logged_in(browser):
    return len(browser.find_elements_by_css_selector("body.logged-in")) > 0


def has_error(browser):
    return len(browser.find_elements_by_css_selector("div.alert-block")) > 0


def get_error(browser):
    return browser.find_element_by_css_selector("div.alert-block").text.strip()


def balances_loaded(browser):
    wallet_block = browser.find_element_by_css_selector("div.lw-card-wallet")
    return len(wallet_block.find_element_by_css_selector("div.lw-amount")
                           .text.strip()) > 0


def validate_accounts(account_ids=None):
    if account_ids is None:
        return
    for account_id in account_ids:
        if account_id not in {"wallet", "offers", "loan"}:
            raise RuntimeError(f"unknown account {account_id}")


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


class Api(providers.Base):
    def __init__(self, browser_factory=None):
        browser_factory = browser_factory or DefaultBrowserFactory()
        self.browser = browser_factory()

    def _is_home(self):
        return self.browser.current_url == CLASSIC_URL

    def _go_home(self):
        if not self._is_home():
            self.browser.get(CLASSIC_URL)
        side_bar = WebDriverWait(self.browser, 60).until(
            presence_of_element_located((By.CSS_SELECTOR, "div.m-lw-db-region-sidebar")))
        WebDriverWait(self.browser, 60).until(balances_loaded)

    def authenticate(self, credentials):
        browser = self.browser
        browser.get(AUTH_URL)
        login_block = WebDriverWait(browser, 60).until(
            presence_of_element_located((By.CSS_SELECTOR, "div.m-lw-login-block")))
        username_input, password_input, *_ = login_block.find_elements_by_tag_name("input")
        username_input.send_keys(credentials.username)
        password_input.send_keys(credentials.password)
        submit_button = browser.find_element_by_css_selector("button.form-submit")
        submit_button.click()
        WebDriverWait(browser, 60).until(any_of(is_logged_in, has_error))
        if not is_logged_in(browser):
            raise AuthFailure(get_error(browser))

    def get_balances(self, account_ids=None):
        def extract_balance(account_id, account_block):
            amount_element = account_block.find_element_by_css_selector("div.lw-amount")
            amount = Price.fromstring(amount_element.text.strip())
            return {
                "account": {
                    "id": account_id,
                    "name": account_id.title(),
                    "iso_currency": "GBP" # TODO,
                },
                "balance": amount.amount_float
            }
        validate_accounts(account_ids)
        self._go_home()
        browser = self.browser
        return {
            "accounts": [
                extract_balance(account_id, block) for (account_id, block) in [
                    ("wallet", browser.find_element_by_css_selector("div.lw-card-wallet")),
                    ("offers", browser.find_element_by_css_selector("div.lw-card-queue")),
                    ("loan", browser.find_element_by_css_selector("div.lw-card-loan"))
                ]
                if account_ids is None or account_id in account_ids
            ]
        }

    def get_transactions(self, account_ids=None):
        validate_accounts(account_ids)
        return {"transactions": []}

    def _get_wallet_assets(self):
        self._go_home()
        browser = self.browser
        amount_str = (browser.find_element_by_css_selector("div.lw-card-wallet")
                             .find_element_by_css_selector("div.lw-amount")
                             .text.strip())
        return [{
            "name": "cash",
            "type": "cash",
            "value": Price.fromstring(amount_str).amount_float,
            "provider_specific": None
        }]

    def _get_offers_assets(self):
        self._go_home()
        browser = self.browser
        amount_str = (browser.find_element_by_css_selector("div.lw-card-queue")
                             .find_element_by_css_selector("div.lw-amount")
                             .text.strip())
        return [{
            "name": "cash",
            "type": "cash",
            "value": Price.fromstring(amount_str).amount_float,
            "provider_specific": None
        }]

    def _get_loan_assets(self):
        cookies = get_cookies(self.browser)
        response = requests.get(LOANS_EXPORT_URL, cookies=cookies)
        csv_data = response.content.decode()
        all_data = list(csv.DictReader(io.StringIO(csv_data)))
        total_outstanding = sum(float(row["Chunk Capital Outstanding"]) for row in all_data)
        return [
            {
                "name": f"{row['Loan ID']}-{row['Chunk ID']}" ,
                "type": "loan",
                "annual_rate": float(row["Chunk Expected Annual Rate"]),
                "value": float(row["Chunk Capital Outstanding"]),
                "provider_specific": deepcopy(dict(row))
            }
            for row in all_data
            if float(row["Chunk Capital Outstanding"]) > 0
        ]

    def get_assets(self, account_ids=None):
        validate_accounts(account_ids)
        return {
            "accounts": [
                {
                    "account": {
                        "id": account_id,
                        "name": account_id.title(),
                        "iso_currency": "GBP"
                    },
                    "assets": handler()
                }
                for account_id, handler in [
                    ("wallet", self._get_wallet_assets),
                    ("offers", self._get_offers_assets),
                    ("loan", self._get_loan_assets)
                ]
                if account_ids is None or account_id in account_ids
            ]
        }

    def get_liabilities(self, account_ids):
        return {"accounts":[]}

    def close(self):
        self.browser.quit()