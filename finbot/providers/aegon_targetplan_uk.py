from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from finbot.providers.support.selenium import any_of, SeleniumHelper
from finbot.providers.errors import AuthFailure
from finbot.core.utils import swallow_exc
from finbot import providers
import logging
import time
import traceback


AUTH_URL = "https://lwp.aegon.co.uk/targetplanUI/login"
BALANCES_URL = "https://lwp.aegon.co.uk/targetplanUI/investments"


@swallow_exc(StaleElementReferenceException)
def _get_login_error(browser_helper: SeleniumHelper):
    error_area = browser_helper.find_maybe(
        By.CSS_SELECTOR, "div#error-container-wrapper")
    if error_area and error_area.is_displayed():
        return error_area.text.strip()


def _is_logged_in(browser_helper: SeleniumHelper):
    avatar_area = browser_helper.find_maybe(By.CSS_SELECTOR, "a#nav-primary-profile")
    return avatar_area is not None


def _wait_accounts(browser_helper: SeleniumHelper):
    accounts_xpath = "//div[contains(@class,'card-product-')]"
    browser_helper.wait_element(By.XPATH, accounts_xpath, timeout=120)
    return browser_helper.find_many(By.XPATH, accounts_xpath)


def _iter_accounts(accounts_elements):
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
                "iso_currency": "GBP"
            },
            "balance": Price.fromstring(balance_str).amount_float,
            "selenium": {
                "ref": account_card,
                "link_element": account_link
            }
        }
    return [extract_account(account_card) for account_card in accounts_elements]


def _iter_assets(assets_table_body):
    for row in assets_table_body.find_elements_by_tag_name("tr"):
        cells = row.find_elements_by_tag_name("td")
        asset_name = (cells[0].find_element_by_tag_name("a")
                                .find_elements_by_tag_name("span")[1]
                                .text.strip())
        yield {
            "name": asset_name,
            "type": "blended fund",
            "units": float(cells[1].text.strip()),
            "value": float(cells[3].text.strip()),
            "provider_specific": {
                "Last price": float(cells[2].text.strip())
            }
        }


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
        self.accounts = None

    def _go_home(self):
        (self.browser.find_element_by_css_selector("div#navbarSupportedContent")
                     .find_element_by_css_selector("div.dropdown")
                     .find_element_by_tag_name("a")
                     .click())

    def _switch_account(self, account_id):
        self._go_home()
        accounts_elements = _wait_accounts(self._do)
        for entry in _iter_accounts(accounts_elements):
            if entry["account"]["id"] == account_id:
                retries = 4
                for _ in range(retries):
                    try:
                        time.sleep(2)
                        entry["selenium"]["link_element"].click()
                        return self._do.wait_element(By.CSS_SELECTOR, "table.table-invs-allocation")
                    except TimeoutException:
                        logging.warning(f"could not go to account page, will try again, trace: {traceback.format_exc()}")
                    except StaleElementReferenceException:
                        logging.warning(f"stale element, we probably managed to get there after all, trace: {traceback.format_exc()}")
                        self._do.wait_element(By.CSS_SELECTOR, "table.table-invs-allocation")
                        return
        raise RuntimeError(f"unknown account {account_id}")

    def authenticate(self, credentials):
        def impl(wait_time):
            self._do.get(AUTH_URL)
            
            # 1. Enter credentials and submit (after specified time period)
            
            login_area = self._do.wait_element(By.CSS_SELECTOR, "form#login")
            username_input, password_input = login_area.find_elements_by_css_selector("input.form-control")
            username_input.send_keys(credentials.username)
            password_input.send_keys(credentials.password)
            submit_button = login_area.find_element_by_tag_name("button")
            time.sleep(wait_time)
            submit_button.click()
            
            # 2. Wait logged-in or error

            self._do.wait_cond(any_of(
                lambda _: _get_login_error(self._do), 
                lambda _: _is_logged_in(self._do)))

            error_message = _get_login_error(self._do)
            if error_message:
                raise AuthFailure(error_message)
            
            # 3. Get accounts data

            accounts_area = _wait_accounts(self._do)
            self.accounts = {
                entry["account"]["id"]: deepcopy(entry["account"])
                for entry in _iter_accounts(accounts_area)
            }

        submit_wait = 1
        trials = 4
        for i in range(trials):
            try:
                return impl(submit_wait)
            except TimeoutException:
                logging.warn(f"timeout while login, re-trying ({i})")
                submit_wait = submit_wait * 2
                pass
        raise RuntimeError(f"unable to login after {trials} trials")

    def get_balances(self):
        self._go_home()
        accounts_elements = _wait_accounts(self._do)
        return {
            "accounts": [
                {
                    "account": deepcopy(entry["account"]),
                    "balance": entry["balance"]
                }
                for entry in _iter_accounts(accounts_elements)
            ]
        }

    def get_assets(self):
        def get_account_assets(account_id, account):
            self._switch_account(account_id)
            assets_table_body = self._do.find(
                By.CSS_SELECTOR, "table.table-invs-allocation > tbody")
            return {
                "account": deepcopy(account),
                "assets": [
                    asset for asset in _iter_assets(assets_table_body)
                ]
            }
        return {
            "accounts": [
                get_account_assets(account_id, account)
                for account_id, account in self.accounts.items()
            ]
        }
