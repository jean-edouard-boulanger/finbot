from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from finbot import providers
from finbot.providers.support.selenium import any_of
from finbot.providers.errors import AuthFailure
import re


AUTH_URL = "https://bank.barclays.co.uk/olb/authlogin/loginAppContainer.do"
HOME_URL = "https://bank.barclays.co.uk/olb/balances/PersonalFinancialSummary.action"


class Credentials(object):
    def __init__(self, last_name, card_number, passcode, memorable_word):
        self.last_name = last_name
        self.card_number = card_number
        self.passcode = passcode
        self.memorable_word = memorable_word

    @property
    def user_id(self):
        return f"{self.last_name} / XXXX-XXXX-XXXX-{self.card_number.split('-')[3]}"

    @staticmethod
    def init(data):
        return Credentials(
            data["last_name"],
            data["card_number"],
            data["passcode"],
            data["memorable_word"])


def _get_passcode_login_button(driver):
    login_buttons = driver.find_elements_by_css_selector("button.btn--login")
    for button in login_buttons:
        if "passcode" in button.text:
            return button
    return None


def _wait_accounts(browser):
    return WebDriverWait(browser, 60).until(
        presence_of_element_located((By.CSS_SELECTOR, "div.accounts-body")))


def _iter_accounts(accounts_area):
    for row in accounts_area.find_elements_by_css_selector("div.o-account__head"):
        account_name = row.find_element_by_css_selector("div.account-link").text
        account_details = row.find_element_by_css_selector("div.o-account__details-body").text.strip().split("\n")
        balance_str = row.find_element_by_css_selector("div.o-account__balance-head").text.strip()
        yield {
            "account": {
                "id": account_details[0],
                "name": account_name,
                "iso_currency": "GBP"
            },
            "balance": Price.fromstring(balance_str).amount_float
        }


def _is_home(browser):
    return HOME_URL in browser.current_url


def _go_home(browser):
    if not _is_home(browser):
        browser.get(HOME_URL)
    return _wait_accounts(browser)


def _get_error(browser):
    warnings = browser.find_elements_by_css_selector("div.notification--warning")
    if len(warnings) > 0:
        return warnings[0].text.strip()
    return None


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = None

    def authenticate(self, credentials):
        def select_combo_item(combo, item_idx):
            for _ in range(item_idx + 1):
                combo.send_keys(Keys.DOWN)
            combo.send_keys(Keys.ENTER)
        browser = self.browser
        browser.get(AUTH_URL)

        # Step 1: last name + card number
        step1_form = WebDriverWait(browser, 60).until(
            presence_of_element_located((By.NAME, "loginStep1")))
        step1_form.find_element_by_css_selector("input#surname0").send_keys(
            credentials.last_name)
        card_radio = step1_form.find_element_by_css_selector("input#radio-c2")
        browser.execute_script("arguments[0].click();", card_radio)
        card_nums = credentials.card_number.split("-")
        for i in range(0, 4):
            step1_form.find_element_by_id(f"cardNumber{i}").send_keys(card_nums[i])
        step1_form.find_element_by_tag_name("button").click()
        passcode_button = WebDriverWait(browser, 60).until(_get_passcode_login_button)
        browser.execute_script("arguments[0].click();", passcode_button)

        WebDriverWait(browser, 60).until(
            any_of(
                presence_of_element_located((By.ID, "passcode0")),
                _get_error(browser)))

        error = _get_error(browser)
        if error is not None:
            raise AuthFailure(error)

        # step 2: authentication (passcode + memorable)
        passcode_input = browser.find_element_by_id("passcode0")
        passcode_input.send_keys(credentials.passcode)
        memorable_label = browser.find_element_by_id("label-memorableCharacters").text.strip()
        char_combos = browser.find_elements_by_id("idForScrollFeature")
        for index, i_str in enumerate(re.findall(r"\d", memorable_label)):
            i = int(i_str) - 1
            item_idx = ord(credentials.memorable_word[i]) - ord('a')
            select_combo_item(char_combos[index], item_idx)
        browser.find_element_by_css_selector("button.btn--login").click()

        # step 3: gather available accounts

        accounts_area = _wait_accounts(self.browser)
        self.accounts = {
            entry["account"]["id"]: entry["account"]
            for entry in _iter_accounts(accounts_area)
        }

    def get_balances(self, account_ids=None):
        accounts_area = _go_home(self.browser)
        return {
            "accounts": [
                {
                    "account": deepcopy(self.accounts[account["account"]["id"]]),
                    "balance": account["balance"]
                }
                for account in _iter_accounts(accounts_area)
                if account_ids is None or account["account"]["id"] in account_ids
            ]
        }

    def get_assets(self, account_ids=None):
        return {
            "accounts": [
                {
                    "account": deepcopy(entry["account"]),
                    "assets": [{
                        "name": "cash",
                        "type": "currency",
                        "value": entry["balance"]
                    }]
                }
                for entry in self.get_balances(account_ids)["accounts"]
            ]
        }
