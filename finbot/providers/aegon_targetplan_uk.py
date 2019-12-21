from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import (
    staleness_of, 
    presence_of_element_located
)
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from finbot.providers.support.selenium import DefaultBrowserFactory, any_of, dump_html
from finbot.providers.errors import AuthFailure
from finbot import providers
from copy import deepcopy
import logging
import time


AUTH_URL = "https://lwp.aegon.co.uk/targetplanUI/login"
BALANCES_URL = "https://lwp.aegon.co.uk/targetplanUI/investments"


def has_error(browser):
    error_area = browser.find_elements_by_css_selector("div#error-container-wrapper")
    if len(error_area) < 1:
        return False
    return error_area[0].is_displayed()


def is_logged_in(browser):
    avatar_area = browser.find_elements_by_css_selector("a#nav-primary-profile")
    return len(avatar_area) > 0 


def iter_accounts(browser):
    def extract_account(account_card):
        card_body = account_card.find_element_by_css_selector("div.card-body")
        card_footer = account_card.find_element_by_css_selector("div.card-footer")
        account_id = card_footer.text.strip().split(" ")[-1]
        account_link = (card_body.find_element_by_tag_name("h3")
                                 .find_element_by_css_selector("a.view-manage-btn"))
        account_name = account_link.text.strip()
        balance_str = card_body.find_element_by_css_selector("div.h1 > span.currency-hero").text.strip()
        return {
            "account": {
                "id": account_id,
                "name": account_name,
                "iso_currency": "GBP" # TODO
            },
            "balance": Price.fromstring(balance_str).amount_float,
            "selenium": {
                "ref": account_card,
                "link_element": account_link
            }
        }
    accounts = browser.find_elements_by_xpath("//div[contains(@class,'card-product-')]")
    return [extract_account(account_card) for account_card in accounts]


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
        self.accounts = None

    def _is_home(self):
        return len(self.browser.find_elements_by_tag_name("h1#page-heading")) > 0

    def _go_home(self):
        if not self._is_home():
            (self.browser.find_element_by_css_selector("div#navbarSupportedContent")
                        .find_element_by_tag_name("div.dropdown")
                        .find_element_by_tag_name("a")
                        .click())
        WebDriverWait(self.browser, 60).until(
            presence_of_element_located((By.XPATH, "//div[contains(@class,'card-product-')]")))

    def _switch_account(self, account_id):
        self._go_home()
        for entry in iter_accounts(self.browser):
            if entry["account"]["id"] == account_id:
                for try_again in range(4):
                    try:
                        time.sleep(1)
                        entry["selenium"]["link_element"].click()
                        WebDriverWait(self.browser, 30).until(
                            presence_of_element_located((By.CSS_SELECTOR, "table.table-invs-allocation")))
                        return
                    except TimeoutException:
                        logging.warn("could not go to account page, will try again")
                    except StaleElementReferenceException:
                        logging.warn("stale element, we probably managed to get there after all")
                        WebDriverWait(self.browser, 30).until(
                            presence_of_element_located((By.CSS_SELECTOR, "table.table-invs-allocation")))
        raise RuntimeError(f"unknown account {account_id}")

    def authenticate(self, credentials):
        browser = self.browser
        browser.get(AUTH_URL)
        login_area = WebDriverWait(browser, 120).until(
            presence_of_element_located((By.CSS_SELECTOR, "form#login")))
        username_input, password_input = login_area.find_elements_by_css_selector("input.form-control")
        username_input.send_keys(credentials.username)
        password_input.send_keys(credentials.password)
        submit_button = login_area.find_element_by_tag_name("button")
        submit_button.click()
        WebDriverWait(browser, 120).until(
            any_of(has_error, is_logged_in))
        if not is_logged_in(browser):
            raise AuthFailure("authentication failure")
        self._go_home()
        self.accounts = {
            entry["account"]["id"]: deepcopy(entry["account"]) 
            for entry in iter_accounts(browser)
        }

    def get_balances(self, account_ids=None):
        self._go_home()
        return {
            "accounts": [
                {
                    "account": deepcopy(entry["account"]),
                    "balance": entry["balance"]
                }
                for entry in iter_accounts(self.browser)
            ]
        }

    def get_assets(self, account_ids=None):
        accounts = []
        for account_id, account in self.accounts.items():
            self._switch_account(account_id)
            assets_table_body = self.browser.find_element_by_css_selector(
                "table.table-invs-allocation > tbody")
            assets = []
            for row in assets_table_body.find_elements_by_tag_name("tr"):
                cells = row.find_elements_by_tag_name("td")
                asset_name = (cells[0].find_element_by_tag_name("a")
                                      .find_elements_by_tag_name("span")[1]
                                      .text.strip())
                assets.append({
                    "name": asset_name,
                    "type": "blended fund",
                    "units": float(cells[1].text.strip()),
                    "value": float(cells[3].text.strip()),
                    "provider_specific": {
                        "Last price": float(cells[2].text.strip())
                    }
                })
            accounts.append({
                "account": deepcopy(account),
                "assets": assets
            })
        return {
            "accounts": accounts
        }

    def get_liabilities(self, account_ids):
        return {"accounts":[]}

    def close(self):
        self.browser.quit()