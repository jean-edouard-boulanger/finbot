from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from finbot.providers.selenium_based import SeleniumBased
from finbot.providers.support.selenium import SeleniumHelper
from finbot.providers.errors import AuthFailure
from finbot.core.utils import swallow_exc
from datetime import datetime, timedelta
from copy import deepcopy
import contextlib
import hashlib
import json
import uuid


BASE_URL = "https://secure.vanguardinvestor.co.uk"


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


class Api(SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home_url = None
        self.account_data = None

    def _go_home(self):
        if self.browser.current_url == self.home_url:
            return
        self._do.get(self.home_url)

    def authenticate(self, credentials):
        def extract_accounts(context_data):
            accounts = []
            for account in context_data["Accounts"]:
                for entry in account["SubAccounts"]:
                    accounts.append(
                        {
                            "description": {
                                "id": entry["SubAccountId"].strip(),
                                "name": entry["PreferredName"].strip(),
                                "iso_currency": "GBP",
                                "type": "investment",
                            },
                            "hierarchy_id": entry["HierarchyId"],
                            "date_created": entry["DateCreated"],
                            "home_url": entry["HomepageUrl"],
                        }
                    )
            return accounts

        browser = self.browser
        browser.get(f"{BASE_URL}/Login")
        auth_form = self._do.wait_element(By.CSS_SELECTOR, "form.form-login")
        user_input, password_input, *_ = auth_form.find_elements_by_tag_name("input")
        user_input.send_keys(credentials.username)
        password_input.send_keys(credentials.password)
        auth_form.find_element_by_css_selector("div.submit button").click()

        self._do.assert_success(
            _is_logged_in, lambda _: _get_login_error(auth_form), _report_auth_error
        )

        self.home_url = self.browser.current_url
        self.account_data = extract_accounts(
            json.loads(
                self._do.find(By.XPATH, "//*[@data-available-context]").get_attribute(
                    "data-available-context"
                )
            )
        )

    def _get_account_balance(self, account):
        dashboard_url = f"{BASE_URL}{account['home_url']}/Dashboard"
        self._do.get(dashboard_url)
        value_cell = self._do.wait_element(
            By.CSS_SELECTOR, "section.portfolio-header div.col-value div.value"
        )
        return {
            "account": deepcopy(account["description"]),
            "balance": Price.fromstring(value_cell.text.strip()).amount_float,
        }

    def get_balances(self):
        return {
            "accounts": [
                self._get_account_balance(account) for account in self.account_data
            ]
        }

    def _get_account_assets(self, account):
        assets_url = f"{BASE_URL}{account['home_url']}/Investments/Holdings"
        self._do.get(assets_url)
        self._do.wait_element(
            By.CSS_SELECTOR, "div.toggle-switch span.label-one"
        ).click()
        investments_table = self._do.wait_element(
            By.CSS_SELECTOR, "table.table-investments-detailed"
        )
        all_assets = []
        for section in investments_table.find_elements_by_css_selector(
            "tbody.group-content"
        ):
            group_row = section.find_element_by_css_selector("tr.group-row")
            product_type = group_row.text.strip().split()[0].lower()
            product_rows = _get_product_rows(section, timedelta(seconds=60))
            for product_row in product_rows:
                all_assets.append(_extract_asset(product_type, product_row))
        return {"account": deepcopy(account["description"]), "assets": all_assets}

    def get_assets(self):
        return {
            "accounts": [
                self._get_account_assets(account) for account in self.account_data
            ]
        }

    def _get_cash_transactions(self, account, from_date, to_date):
        cash_txn_url = f"{BASE_URL}{account['home_url']}/Transactions/Cash"
        self._do.get(cash_txn_url)
        staleness_detector = _StalenessDetector(self._do)
        transactions_table = self._do.wait_element(
            By.CSS_SELECTOR, "table.table-transactions > tbody"
        )
        while True:
            extractor = _extract_cash_transactions(
                transactions_table, staleness_detector
            )
            try:
                for transaction in extractor:
                    # vanguard displays transactions latest first, if the current
                    # transaction's date is less than the lower bound, there is
                    # no need to go further
                    if transaction["date"] < from_date:
                        return
                    if transaction["date"] <= to_date:
                        yield transaction
            except StaleElementReferenceException:
                # When reaching the last page of transactions, some rows in the
                # transactions table will become stale, raising this exception.
                # TODO: until there is a better solution, this simply indicates
                # the end of the transactions list
                return
            next_button = self._do.find(By.CSS_SELECTOR, "button.next")
            if not next_button.is_enabled():
                return
            next_button.click()

    def _get_account_transactions(self, account, from_date, to_date):
        return {
            "account": deepcopy(account["description"]),
            "transactions": list(
                self._get_cash_transactions(account, from_date, to_date)
            ),
        }

    def get_transactions(self, from_date, to_date):
        return {
            "accounts": [
                self._get_account_transactions(account, from_date, to_date)
                for account in self.account_data
            ]
        }


class _StalenessDetector(object):
    def __init__(self, browser_helper: SeleniumHelper):
        self._browser_helper = browser_helper
        self._marker = str(uuid.uuid4())

    def mark_visited(self, element):
        self._browser_helper.execute_script(
            f"arguments[0].innerHTML = '{self._marker}'", element
        )

    def wait_refreshed(self, element):
        self._browser_helper.wait_cond(lambda _: element.text.strip() != self._marker)

    @contextlib.contextmanager
    def visit(self, element):
        self.wait_refreshed(element)
        yield
        self.mark_visited(element)


def _get_product_rows(section, timeout: timedelta):
    cutoff = datetime.now() + timeout
    while datetime.now() < cutoff:
        product_rows = section.find_elements_by_css_selector("tr.product-row")
        if len(product_rows) > 0:
            return product_rows
    raise RuntimeError("could not find product rows in section")


def _extract_cash_asset(product_row):
    amount_str = product_row.find_elements_by_tag_name("td")[5].text.strip()
    return {
        "name": "Cash",
        "type": "currency",
        "value": Price.fromstring(amount_str).amount_float,
    }


def _extract_fund_asset(product_type, product_row):
    cells = product_row.find_elements_by_tag_name("td")
    name_cell = cells[0].find_element_by_css_selector("p.content-product-name")
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
            "Average unit cost": avg_unit_cost,
        },
    }


def _extract_cash_transactions(
    transactions_table, staleness_detector: _StalenessDetector
):
    for row in transactions_table.find_elements_by_tag_name("tr"):
        cells = row.find_elements_by_tag_name("td")
        with staleness_detector.visit(cells[0]):
            txn_date = datetime.strptime(cells[0].text.strip(), "%d %B %Y")
            txn_description = cells[1].text.strip()
            txn_in_amount = Price.fromstring(cells[2].text.strip()).amount_float
            txn_out_amount = Price.fromstring(cells[3].text.strip()).amount_float
            txn_amount = (
                txn_in_amount if txn_in_amount is not None else (txn_out_amount * -1.0)
            )
            txn_type = "credit" if txn_in_amount is not None else "debit"
            txn_bal = Price.fromstring(cells[4].text.strip()).amount_float
            txn_id = (
                "VGXX-"
                + hashlib.sha224(
                    "/".join(
                        [
                            txn_date.isoformat(),
                            txn_description,
                            str(txn_amount),
                            txn_type,
                            str(txn_bal),
                        ]
                    ).encode()
                ).hexdigest()
            )
            yield {
                "id": txn_id,
                "date": txn_date,
                "description": txn_description,
                "amount": txn_amount,
                "type": txn_type,
            }


def _extract_asset(product_type, product_row):
    if product_type == "cash":
        return _extract_cash_asset(product_row)
    return _extract_fund_asset(product_type, product_row)


@swallow_exc(StaleElementReferenceException)
def _get_login_error(auth_form):
    error_area = auth_form.find_elements_by_class_name("error-message")
    if error_area and error_area[0].is_displayed():
        return error_area[0].text.strip()


def _report_auth_error(error_message):
    raise AuthFailure(error_message.replace("\n", " ").strip())


def _is_logged_in(do: SeleniumHelper):
    return do.find_maybe(By.CSS_SELECTOR, "section.portfolio-header") is not None
