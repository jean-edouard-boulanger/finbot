from finbot import providers
from finbot.providers.support.selenium import any_of, SeleniumHelper
from finbot.providers.errors import AuthFailure, Error
from finbot.core.utils import in_range
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.common.by import By
from datetime import datetime
from copy import deepcopy
from price_parser import Price
import re


AUTH_URL = "https://global.americanexpress.com/login"
HOME_URL = "https://global.americanexpress.com/dashboard"


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = None

    def _go_home(self):
        if "dashboard" in self.browser.current_url:
            return
        self._do.get(HOME_URL)
        self._do.wait_element(By.CSS_SELECTOR, "section.balance-container")

    def _switch_account(self, account_id):
        self._go_home()
        for entry in _iter_accounts(self._do):
            if entry["account"]["id"] == account_id:
                self._do.click(entry["selenium"]["account_element_ref"])
                return self._do.wait_element(By.CSS_SELECTOR, "section.balance-container")
        raise Error(f"unable to switch to account {account_id}")

    def authenticate(self, credentials):
        self._do.get(AUTH_URL)
        cookies_mask = self._do.wait_element(By.ID, "euc_mask")
        cookies_mask.click()

        self._do.find(By.ID, "eliloUserID").send_keys(credentials.user_id)
        self._do.find(By.ID, "eliloPassword").send_keys(credentials.password)
        self._do.find(By.ID, "loginSubmit").click()

        self._do.wait_cond(any_of(
            presence_of_element_located((By.CSS_SELECTOR, "section.balance-container")),
            lambda _: _get_login_error(self._do)))

        error_message = _get_login_error(self._do)
        if error_message:
            raise AuthFailure(error_message)

        self.accounts = {
            entry["account"]["id"]: deepcopy(entry["account"])
            for entry in _iter_accounts(self._do)
        }

    def get_balances(self):
        accounts = []
        for account_id, account in self.accounts.items():
            balance = _get_balance(self._switch_account(account_id))
            accounts.append({
                "account": deepcopy(account),
                "balance": balance.amount_float * -1.0
            })
        return {"accounts": accounts}

    def get_liabilities(self):
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
                for entry in self.get_balances()["accounts"]
            ]
        }

    def _get_account_transactions(self, account_id, from_date, to_date):
        def parse_transaction_date(date_str):
            return datetime.strptime(date_str, "%d %b %y") 

        def extract_transaction_header(row):
            summary_id = row.get_attribute("id")
            details_id = summary_id.replace("trans", "etd")
            date_cell, description_cell, amount_cell = row.find_elements_by_tag_name("td")
            txn_amount = Price.fromstring(amount_cell.text).amount_float
            return {
                "date": parse_transaction_date(date_cell.text.strip()),
                "amount": txn_amount,
                "description": description_cell.text.strip(),
                "type": "debit" if txn_amount >= 0 else "credit",
                "details_id": details_id,
                "selenium": {
                    "header_row_ref": row
                }
            }

        def extract_transaction(txn_header):
            self._do.click(txn_header["selenium"]["header_row_ref"])
            details_row = self._do.wait_element(By.ID, txn_header["details_id"])
            clean_details = " ".join(entry.strip() for entry in details_row.text.split("\n"))
            txn_id = re.findall(r"REFERENCE NUMBER:\s+(\w+)\s+", clean_details)[0]
            return {
                "id": txn_id,
                "date": txn_header["date"],
                "description": txn_header["description"],
                "amount": txn_header["amount"],
                "type": txn_header["type"]
            }

        # 1. go to all transactions page

        self._switch_account(account_id)
        links_area = self._do.wait_element(By.CSS_SELECTOR, "div.transaction-footer-links")
        transactions_link = links_area.find_element_by_xpath(
            "//a[contains(@title, 'recent activity')]")
        self._do.click(transactions_link)

        # 2. get full transaction list
    
        while True:
            more_button = self._do.find_maybe(By.XPATH, "//button[contains(@title, 'more transactions')]")
            if not more_button or not more_button.is_displayed():
                break
            self._do.click(more_button)

        # 3. expand all transactions

        transactions_table = self._do.wait_element(By.ID, "transaction-table")
        txn_rows = transactions_table.find_elements_by_css_selector("tr.transaction-list-row")
        
        txn_in_scope = []
        for txn_row in txn_rows:
            txn_header = extract_transaction_header(txn_row)
            if in_range(txn_header["date"], from_date, to_date):
                txn_in_scope.append(txn_header)

        return [
            extract_transaction(txn_header) 
            for txn_header in txn_in_scope
        ]

    def get_transactions(self, from_date=None, to_date=None):
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


def _iter_accounts(browser_helper: SeleniumHelper):
    accounts_switcher_area = browser_helper.wait_element(
        By.CSS_SELECTOR, "section.axp-account-switcher")
    accounts_switcher = accounts_switcher_area.find_element_by_tag_name("button")
    browser_helper.click(accounts_switcher)

    accounts_area = browser_helper.wait_element(By.ID, "accounts")
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
                "iso_currency": "GBP",
                "type": "credit"
            },
            "selenium": {
                "account_element_ref": account_row
            }
        }

    browser_helper.click(accounts_switcher)


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


def _get_login_error(browser_helper: SeleniumHelper):
    alert_area = browser_helper.find_maybe(By.CSS_SELECTOR, "div.alert")
    if alert_area:
        return alert_area.text
