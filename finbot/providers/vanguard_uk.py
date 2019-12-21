from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import (
    staleness_of, 
    presence_of_element_located
)
from selenium.common.exceptions import StaleElementReferenceException
from finbot.providers.support.selenium import DefaultBrowserFactory, any_of, dump_html
from finbot.providers.errors import AuthFailure
from finbot import providers
import json
import logging


BASE_URL = "https://secure.vanguardinvestor.co.uk"


def get_login_error(auth_form):
    try:
        error_area = auth_form.find_elements_by_class_name("error-message")
        if len(error_area) < 1 or not error_area[0].is_displayed():
            return None
        return error_area[0].text.strip()
    except StaleElementReferenceException:
        return None


class has_login_error(object):
    def __init__(self, auth_form):
        self.auth_form = auth_form
    def __call__(self, driver):
        return get_login_error(self.auth_form) is not None


class Session(object):
    def __init__(self, is_auth=False, home_url=None, context_data=None):
        self.is_authenticated = is_auth
        self.home_url = None
        self.account_data = None

    def get_account(self, account_id):
        for account in self.account_data:
            if account["id"] == account_id:
                return account
        raise KeyError(f"could not find account {account_id}")


def json_dumps(data):
    return json.dumps(data, indent=4)


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
        self.session = Session()
    
    def _go_home(self):
        if self.browser.current_url == self.session.home_url:
            return
        self.browser.get(self.session.home_url)

    def is_authenticated(self):
        return self.session.is_authenticated

    def authenticate(self, credentials):
        def extract_accounts(context_data):
            accounts = []
            for account in context_data["Accounts"]:
                for entry in account["SubAccounts"]:
                    accounts.append({
                        "hierarchy_id": entry["HierarchyId"],
                        "name": entry["PreferredName"].strip(),
                        "id": entry["SubAccountId"],
                        "date_created": entry["DateCreated"],
                        "home_url": entry["HomepageUrl"]
                    })
            return accounts

        assert not self.session.is_authenticated
        browser = self.browser
        browser.get(f"{BASE_URL}/Login")
        auth_form = WebDriverWait(browser, 60).until(
            presence_of_element_located((By.CSS_SELECTOR, "form.form-login")))
        user_input, password_input, *_ = auth_form.find_elements_by_tag_name("input")
        user_input.send_keys(credentials.username)
        password_input.send_keys(credentials.password)
        (auth_form.find_element_by_class_name("submit")
                  .find_element_by_css_selector("button")
                  .click())
        WebDriverWait(browser, 120).until(
            any_of(
                staleness_of(auth_form),
                has_login_error(auth_form)))
        if has_login_error(auth_form)(browser):
            raise AuthFailure(get_login_error(auth_form))
        self.session.is_authenticated = True
        self.session.home_url = self.browser.current_url
        self.session.account_data = extract_accounts(json.loads(
            browser.find_element_by_xpath("//*[@data-available-context]")
                   .get_attribute("data-available-context")))

    def get_balances(self):
        def extract_account_balance(summary_row):
            cells = summary_row.find_elements_by_tag_name("td")
            account_name = cells[0].find_element_by_css_selector("a.account-name").text
            account_id = cells[0].find_element_by_css_selector("span.account-code").text
            balance = Price.fromstring(cells[2].text)
            return {
                "account": {
                    "id": account_id,
                    "name": account_name,
                    "iso_currency": "GBP" # TODO
                },
                "balance": balance.amount_float
            }

        assert self.session.is_authenticated
        self._go_home()
        browser = self.browser
        balances_table = WebDriverWait(browser, 60).until(
            presence_of_element_located((By.CLASS_NAME, "table-multi-product")))
        balances_table_body = balances_table.find_element_by_tag_name("tbody")
        return {
            "accounts": [
                extract_account_balance(row)
                for row in balances_table_body.find_elements_by_tag_name("tr")
            ]
        }

    def get_transactions(self, account_ids=None):
        return {"accounts": []}

    def _get_assets_for_account(self, account):
        def extract_cash_asset(product_row):
            amount_str = product_row.find_elements_by_tag_name("td")[5].text.strip()
            return {
                "name": "cash",
                "type": "cash",
                "value": Price.fromstring(amount_str).amount_float,
            }
        def extract_fund_asset(product_type, product_row):
            cells = product_row.find_elements_by_tag_name("td")
            name_cell = cells[0].find_element_by_css_selector(
                "div.product-info-wrapper > p.content-product-name")
            product_name = name_cell.text.strip()
            ongoing_charges = float(cells[1].text.strip()[:-1]) / 100.0
            units = float(cells[2].text.strip())
            avg_unit_cost = Price.fromstring(cells[3].text.strip()).amount_float
            last_price = Price.fromstring(cells[4].text.strip()).amount_float
            total_cost = Price.fromstring(cells[5].text.strip()).amount_float
            value = Price.fromstring(cells[6].text.strip()).amount_float
            return {
                "name": product_name,
                "type": f"{product_type} fund",
                "units": units,
                "value": value,
                "provider_specific": {
                    "Ongoing charges": ongoing_charges,
                    "Last price": last_price,
                    "Total cost": total_cost,
                    "Average unit cost": avg_unit_cost
                }
            }

        def extract_asset(product_type, product_row):
            if product_type == "cash":
                return extract_cash_asset(product_row)
            return extract_fund_asset(product_type, product_row)

        assets_url = f"{BASE_URL}{account['home_url']}/Investments/Holdings"
        browser = self.browser
        browser.get(assets_url)
        toggle_switch = WebDriverWait(browser, 60).until(
            presence_of_element_located((By.CSS_SELECTOR, "div.toggle-switch")))
        toggle_switch.find_element_by_css_selector("span.label-one").click()
        investments_table = WebDriverWait(browser, 60).until(
            presence_of_element_located((By.CSS_SELECTOR, "table.table-investments-detailed")))
        product_type = None
        all_assets = []
        for row in investments_table.find_elements_by_tag_name("tr"):
            class_name = row.get_attribute("class")
            if class_name == "group-row":
                product_type = row.find_element_by_tag_name("td > span > span").text.strip().lower()
            if class_name == "product-row":
                assert product_type is not None
                all_assets.append(extract_asset(product_type, row))
        return {
            "account": {
                "id": account["id"],
                "name": account["name"],
                "iso_currency": "GBP"
            },
            "assets": all_assets
        }

    def get_assets(self, account_ids=None):
        return {
            "accounts": [
                self._get_assets_for_account(account)
                for account in self.session.account_data
                if account_ids is None or account["id"] in account_ids
            ]
        }

    def get_liabilities(self, account_ids):
        return {"accounts":[]}

    def close(self):
        self.browser.quit()