from finbot.providers.selenium_based import SeleniumBased
from finbot.providers.support.selenium import SeleniumHelper
from finbot.providers.errors import AuthenticationFailure
from finbot import providers
from finbot.core.utils import swallow_exc

from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

from price_parser import Price  # type: ignore

from typing import Any, Optional, Iterator
from datetime import datetime, timedelta
from copy import deepcopy
import contextlib
import json
import uuid


BASE_URL = "https://secure.vanguardinvestor.co.uk"


class Credentials(object):
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    @property
    def user_id(self) -> str:
        return self.username

    @staticmethod
    def init(data: dict[Any, Any]) -> "Credentials":
        return Credentials(data["username"], data["password"])


class Api(SeleniumBased):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.home_url: Optional[str] = None
        self.account_data: Optional[list[dict[str, Any]]] = None

    def _go_home(self) -> None:
        assert self.home_url is not None
        if self.browser.current_url == self.home_url:
            return
        self._do.get(self.home_url)

    def authenticate(self, credentials: Credentials) -> None:
        def extract_accounts(context_data: dict[str, Any]) -> list[dict[str, Any]]:
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
                            "home_url": entry["HomepageUrl"],
                        }
                    )
            return accounts

        browser = self.browser
        browser.get(f"{BASE_URL}/Login")
        auth_form = self._do.wait_element(By.CSS_SELECTOR, "form.form-login")
        user_input, password_input, *_ = auth_form.find_elements(By.TAG_NAME, "input")
        user_input.send_keys(credentials.username)
        password_input.send_keys(credentials.password)
        auth_form.find_element(By.CSS_SELECTOR, "div.submit button").click()

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

    def _get_account_balance(self, account: dict[str, Any]) -> providers.BalanceEntry:
        dashboard_url = f"{BASE_URL}{account['home_url']}/Dashboard"
        self._do.get(dashboard_url)
        value_cell = self._do.wait_element(
            By.CSS_SELECTOR, "section.portfolio-header div.col-value div.value"
        )
        account_description: providers.Account = deepcopy(account["description"])
        account_balance = Price.fromstring(value_cell.text.strip()).amount_float
        assert account_balance is not None
        return {
            "account": account_description,
            "balance": account_balance,
        }

    def get_balances(self) -> providers.Balances:
        assert self.account_data is not None
        return {
            "accounts": [
                self._get_account_balance(account) for account in self.account_data
            ]
        }

    def _get_account_assets(self, account: dict[str, Any]) -> providers.AssetEntry:
        assets_url = f"{BASE_URL}{account['home_url']}/Investments/Holdings"
        self._do.get(assets_url)
        self._do.wait_element(
            By.CSS_SELECTOR, "div.toggle-switch span.label-one"
        ).click()
        investments_table = self._do.wait_element(
            By.CSS_SELECTOR, "table.table-investments-detailed"
        )
        all_assets: list[providers.Asset] = []
        for section in investments_table.find_elements(
            By.CSS_SELECTOR, "tbody.group-content"
        ):
            group_row = section.find_element(By.CSS_SELECTOR, "tr.group-row")
            product_type = group_row.text.strip().split()[0].lower()
            product_rows = _get_product_rows(section, timedelta(seconds=60))
            for product_row in product_rows:
                all_assets.append(_extract_asset(product_type, product_row))
        account_description: providers.Account = deepcopy(account["description"])
        return {"account": account_description, "assets": all_assets}

    def get_assets(self) -> providers.Assets:
        assert self.account_data is not None
        return {
            "accounts": [
                self._get_account_assets(account) for account in self.account_data
            ]
        }


class _StalenessDetector(object):
    def __init__(self, browser_helper: SeleniumHelper):
        self._browser_helper = browser_helper
        self._marker = str(uuid.uuid4())

    def mark_visited(self, element: WebElement) -> None:
        self._browser_helper.execute_script(
            f"arguments[0].innerHTML = '{self._marker}'", element
        )

    def wait_refreshed(self, element: WebElement) -> None:
        self._browser_helper.wait_cond(lambda _: element.text.strip() != self._marker)

    @contextlib.contextmanager
    def visit(self, element: WebElement) -> Iterator[None]:
        self.wait_refreshed(element)
        yield
        self.mark_visited(element)


def _get_product_rows(section: WebElement, timeout: timedelta) -> list[WebElement]:
    cutoff = datetime.now() + timeout
    while datetime.now() < cutoff:
        product_rows: list[WebElement] = section.find_elements(
            By.CSS_SELECTOR, "tr.product-row"
        )
        if len(product_rows) > 0:
            return product_rows
    raise RuntimeError("could not find product rows in section")


def _extract_cash_asset(product_row: WebElement) -> providers.Asset:
    amount_str = product_row.find_elements(By.TAG_NAME, "td")[5].text.strip()
    amount = Price.fromstring(amount_str).amount_float
    assert amount is not None
    return {
        "name": "Cash",
        "type": "currency",
        "value": amount,
    }


def _extract_fund_asset(product_type: str, product_row: WebElement) -> providers.Asset:
    cells = product_row.find_elements(By.TAG_NAME, "td")
    name_cell = cells[0].find_element(By.CSS_SELECTOR, "p.content-product-name")
    product_name = name_cell.text.strip()
    ongoing_charges = float(cells[1].text.strip()[:-1]) / 100.0
    units = float(cells[2].text.strip())
    avg_unit_cost = Price.fromstring(cells[3].text.strip()).amount_float
    last_price = Price.fromstring(cells[4].text.strip()).amount_float
    total_cost = Price.fromstring(cells[5].text.strip()).amount_float
    value = Price.fromstring(cells[6].text.strip()).amount_float
    assert value is not None
    return {
        "name": product_name,
        "type": f"{product_type} fund",
        "value": value,
        "units": units,
        "provider_specific": {
            "Ongoing charges": ongoing_charges,
            "Last price": last_price,
            "Total cost": total_cost,
            "Average unit cost": avg_unit_cost,
        },
    }


def _extract_asset(product_type: str, product_row: WebElement) -> providers.Asset:
    if product_type == "cash":
        return _extract_cash_asset(product_row)
    return _extract_fund_asset(product_type, product_row)


@swallow_exc(StaleElementReferenceException)
def _get_login_error(auth_form: WebElement) -> Optional[str]:
    error_area: list[WebElement] = auth_form.find_elements(
        By.CLASS_NAME, "error-message"
    )
    if error_area and error_area[0].is_displayed():
        login_error: str = error_area[0].text.strip()
        return login_error
    return None


def _report_auth_error(error_message: str) -> None:
    raise AuthenticationFailure(error_message.replace("\n", " ").strip())


def _is_logged_in(do: SeleniumHelper) -> bool:
    return do.find_maybe(By.CSS_SELECTOR, "section.portfolio-header") is not None
