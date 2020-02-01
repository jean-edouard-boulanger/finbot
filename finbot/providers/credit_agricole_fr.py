from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import staleness_of
from finbot.providers.support.selenium import (
    any_of, 
    all_of, 
    negate
)
from finbot import providers
from finbot.providers.errors import AuthFailure


BASE_URL = "https://www.ca-cb.fr/"


def _is_logged_in(browser):
    account_button = browser.find_elements_by_css_selector("li#bnc-compte")
    return len(account_button) > 0 


def _get_account_rows(browser):
    ca_table = browser.find_element_by_css_selector("table.ca-table")
    even_rows = ca_table.find_elements_by_css_selector("tr.colcellignepaire")
    odd_rows = ca_table.find_elements_by_css_selector("tr.colcelligneimpaire")
    return even_rows + odd_rows


def _iter_accounts(browser):
    for row in _get_account_rows(browser):
        cells = row.find_elements_by_tag_name("td")
        account_name = cells[0].find_element_by_tag_name("a").text.strip()
        account_id_link = cells[2].find_element_by_tag_name("a")
        account_id = account_id_link.text.strip()
        amount = Price.fromstring(cells[4].find_element_by_tag_name("a").text.strip())
        ccy = cells[5].find_element_by_tag_name("a").text.strip()
        yield {
            "account": {
                "id": account_id,
                "name": account_name,
                "iso_currency": ccy
            },
            "balance": amount.amount_float,
            "selenium": {
                "ref": row,
                "link_element": account_id_link
            }
        }


def _map_keypad_buttons(keypad_table):
    mapping = {}
    for row in keypad_table.find_elements_by_tag_name("tr"):
        for cell in row.find_elements_by_tag_name("td"):
            link = cell.find_element_by_tag_name("a")
            value = link.text.strip()
            if len(value) > 0:
                mapping[value] = link
    return mapping


class Credentials(object):
    def __init__(self, account_number, password):
        self.account_number = account_number
        self.password = password

    @property
    def user_id(self):
        return self.account_number

    @staticmethod
    def init(data):
        return Credentials(data["account_number"], data["password"])


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = None

    def _go_home(self):
        self.browser.find_element_by_css_selector("a#bnc-compte-href").click()
        self._do.wait_element(By.CSS_SELECTOR, "table.ca-table")

    def _switch_account_with_selector(self, account_id, account_selector):
        for option in account_selector.find_elements_by_tag_name("option"):
            option_text = option.text
            if account_id in option_text:
                return option.click()
        raise RuntimeError(f"unable to find account {account_id}")

    def _switch_account_via_home(self, account_id):
        self._go_home()
        for account_entry in _iter_accounts(self.browser):
            if account_entry["account"]["id"] == account_id:
                return account_entry["selenium"]["link_element"].click()
        raise RuntimeError(f"unable to find account {account_id}")

    def _switch_account(self, account_id):
        account_selector = self._do.find_maybe(By.CSS_SELECTOR, "select#lstCpte")
        if account_selector:
            self._switch_account_with_selector(account_id, account_selector)
        else:
            self._switch_account_via_home(account_id)
        return self._do.wait_element(By.CSS_SELECTOR, "div.ca-forms")

    def authenticate(self, credentials):
        browser = self.browser
        browser.get(BASE_URL)
        browser.find_element_by_id("acces_aux_comptes").find_element_by_tag_name("a").click()
        keypad_table = self._do.wait_element(By.CSS_SELECTOR, "table#pave-saisie-code")
        links_mapping = _map_keypad_buttons(keypad_table)
        for digit in str(credentials.password):
            links_mapping[digit].click()
        browser.find_element_by_name("CCPTE").send_keys(credentials.account_number)
        submit_area = browser.find_element_by_css_selector("p.validation.clearboth")
        submit_link = (submit_area.find_element_by_css_selector("span.droite")
                                  .find_elements_by_tag_name("a")[1])
        root_area = browser.find_element_by_css_selector("div#container")
        submit_link.click()
        self._do.wait().until(any_of(
            _is_logged_in,
            all_of(staleness_of(root_area), negate(_is_logged_in))))

        if not _is_logged_in(browser):
            raise AuthFailure()

        self.accounts = {
            entry["account"]["id"]: entry["account"]
            for entry in _iter_accounts(self.browser)
        }

    def get_balances(self, account_ids=None):
        self._go_home()
        return {
            "accounts": [
                {
                    "account": deepcopy(entry["account"]),
                    "balance": entry["balance"]
                }
                for entry in _iter_accounts(self.browser)
            ]
        }

    def get_assets(self):
        return {
            "accounts": [
                {
                    "account": deepcopy(entry["account"]),
                    "assets": [{
                        "name": "cash",
                        "type": "currency",
                        "value": entry["balance"],
                    }]
                }
                for entry in self.get_balances()["accounts"]
            ]
        }
