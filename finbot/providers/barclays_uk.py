from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from finbot import providers
from finbot.providers.support.selenium import any_of
from finbot.providers.errors import AuthFailure, Error
from finbot.core.utils import date_in_range
from datetime import datetime
import re
import hashlib
import code


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
        account_cell = row.find_element_by_css_selector("div.account-link")
        account_link_element = account_cell.find_element_by_tag_name("a")
        account_details = row.find_element_by_css_selector("div.o-account__details-body").text.strip().split("\n")
        balance_str = row.find_element_by_css_selector("div.o-account__balance-head").text.strip()
        yield {
            "account": {
                "id": account_details[0],
                "name": account_cell.text.strip(),
                "iso_currency": "GBP"
            },
            "balance": Price.fromstring(balance_str).amount_float,
            "selenium": {
                "account_link": account_link_element
            }
        }

def _get_error(browser):
    warnings = browser.find_elements_by_css_selector("div.notification--warning")
    if len(warnings) > 0:
        return warnings[0].text.strip()
    return None


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = None

    def _go_home(self):
        browser = self.browser
        browser.get(HOME_URL)
        return _wait_accounts(browser)

    def _switch_account(self, account_id):
        accounts_area = self._go_home()
        for entry in _iter_accounts(accounts_area):
            if entry["account"]["id"] == account_id:
                entry["selenium"]["account_link"].click()
                return self._wait_element(By.CSS_SELECTOR, "div.transactions-table")
        raise Error(f"unable to switch to account '{account_id}'")

    def authenticate(self, credentials):
        def select_combo_item(combo, item_idx):
            for _ in range(item_idx + 1):
                combo.send_keys(Keys.DOWN)
            combo.send_keys(Keys.ENTER)
        browser = self.browser
        browser.get(AUTH_URL)

        # Step 1: last name + card number
        step1_form = self._wait_element(By.NAME, "loginStep1")
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

        self._wait().until(any_of(
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

    def _get_account_transactions(self, account_id, from_date, to_date):
        all_txn = []
        transactions_table = self._switch_account(account_id)
        body_area = transactions_table.find_element_by_css_selector("div.tbody-trans")
        for row in body_area.find_elements_by_css_selector("div.row"):
            header_row = row.find_element_by_css_selector("div.th-wrapper")
            cells = header_row.find_elements_by_tag_name("div.th")
            _, date_cell, desc_cell, in_cell, out_cell, bal_cell = cells
            txn_date = datetime.strptime(date_cell.text.strip(), "%a, %d %b %y")
            if not date_in_range(txn_date, from_date, to_date):
                continue
            txn_in_amount = Price.fromstring(in_cell.text.strip()).amount_float
            txn_out_amount = Price.fromstring(out_cell.text.strip()).amount_float
            txn_amount = txn_in_amount if txn_in_amount is not None else (txn_out_amount * -1.0)
            txn_type = "credit" if txn_in_amount is not None else "debit"

            more_data_cells = row.find_elements_by_css_selector(
                "span.additional-data-content")
            txn_type_cell = more_data_cells[1]
            txn_description = desc_cell.text.strip()
            if len(more_data_cells) > 2:
                txn_description += f" ({more_data_cells[2].get_attribute('innerText').strip()})"

            # generate synthetic transaction identifier

            txn_id = hashlib.sha256("/".join([
                txn_date.isoformat(),
                txn_description,
                str(txn_amount),
                txn_type,
                txn_type_cell.text.strip(),
                str(Price.fromstring(bal_cell.text.strip()).amount_float)
            ]).encode()).hexdigest()

            all_txn.append({
                "id": txn_id,
                "date": txn_date,
                "description": txn_description,
                "amount": txn_amount,
                "type": txn_type,
            })
        return all_txn

    def get_transactions(self, from_date, to_date):
        return {
            "accounts": [
                {
                    "account": deepcopy(account),
                    "transactions": self._get_account_transactions(
                        account_id, from_date, to_date)
                }
                for account_id, account in self.accounts.items()
            ]
        }

    def get_balances(self):
        accounts_area = self._go_home()
        return {
            "accounts": [
                {
                    "account": deepcopy(self.accounts[account["account"]["id"]]),
                    "balance": account["balance"]
                }
                for account in _iter_accounts(accounts_area)
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
                        "value": entry["balance"]
                    }]
                }
                for entry in self.get_balances()["accounts"]
            ]
        }
