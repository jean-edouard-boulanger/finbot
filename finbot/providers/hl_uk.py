from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from finbot.providers.support.selenium import SeleniumHelper
from finbot.providers.errors import Error
from finbot import providers
from finbot.providers.errors import AuthFailure
import re


AUTH_URL = "https://online.hl.co.uk/my-accounts/login-step-one"


class Credentials(object):
    def __init__(self, username, birth_date, online_password, secret_number):
        self.username = username
        self.birth_date = birth_date
        self.online_password = online_password
        self.secret_number = secret_number

    @property
    def user_id(self):
        return self.username

    @staticmethod
    def init(data):
        return Credentials(data["username"],
                           data["birth_date"],
                           data["online_password"],
                           data["secret_number"])


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accounts = None

    def authenticate(self, credentials: Credentials):
        self._do.get(AUTH_URL)

        # step 1: provide username and password

        self._do.wait_element(By.ID, "username").send_keys(credentials.username)
        self._do.find(By.ID, "date-of-birth").send_keys(credentials.birth_date)
        self._do.find(By.XPATH, "//input[@type='submit']").click()

        self._do.assert_success(_reached_auth_step2, _get_login_error,
                                on_failure=_report_auth_error)

        # step 2: provide online password and secret number

        _get_online_password_input(self._do).send_keys(credentials.online_password)
        secret_number_inputs = self._do.find_many(By.CSS_SELECTOR, "input.secure-number-container__input")
        for index, digit_input in enumerate(secret_number_inputs):
            if digit_input.is_enabled():
                digit_input.send_keys(credentials.secret_number[index])

        submit_button = self._do.find(By.XPATH, "//input[@type='submit']")
        self._do.click(submit_button)

        self._do.assert_success(_is_logged_in, _get_login_error,
                                on_failure=_report_auth_error)

        accounts_table = _get_accounts_table(self._do)
        self.accounts = [entry for entry in _iter_accounts(accounts_table)]

    def _iter_accounts_details(self):
        for entry in self.accounts:
            yield entry["account"], _get_account_details(self._do, entry)

    def get_balances(self):
        return {
            "accounts": [
                {
                    "account": account,
                    "balance": details["balance"]
                }
                for account, details in self._iter_accounts_details()
            ]
        }

    def get_assets(self):
        return {
            "accounts": [
                {
                    "account": account,
                    "assets": details["assets"]
                }
                for account, details in self._iter_accounts_details()
            ]
        }


def _make_cash_position(amount):
    return {
        "name": "Cash",
        "type": "currency",
        "value": amount
    }


def _get_cash_account_details(account):
    return {
        "balance": account["balance"],
        "assets": [_make_cash_position(account["balance"])]
    }


def _get_assets_from_holdings_table(holdings_table: WebElement):
    rows = holdings_table.find_elements_by_css_selector("tbody tr")
    for row in rows:
        cells = row.find_elements_by_tag_name("td")
        if len(cells) == 1:
            # needed in the case the holdings table is empty
            # (only contains an informative message)
            return
        yield {
            "name": cells[1].text.strip(),
            "type": "stock",
            "units": float(cells[2].text.strip()),
            "value": Price.fromstring(cells[4].text.strip()),
            "provider_specific": {
                "Total cost (£)": Price.fromstring(cells[5].text.strip()).amount_float,
                "P&L (£)": Price.fromstring(cells[6].text.strip()).amount_float,
                "P&L (%)": float(cells[7].text.strip())
            }
        }


def _get_investment_account_details(do: SeleniumHelper, account):
    do.get(account["summary_url"])
    cash_value_str = do.wait_element(By.ID, "cash_total_header").text.strip()
    cash_value = Price.fromstring(cash_value_str).amount_float
    stocks_value_str = do.wait_element(By.ID, "stock_total_header").text.strip()
    stocks_value = Price.fromstring(stocks_value_str).amount_float
    holdings_table = do.wait_element(By.ID, "holdings-table")

    return {
        "balance": cash_value + stocks_value,
        "assets": [_make_cash_position(cash_value)] + list(_get_assets_from_holdings_table(holdings_table))
    }


def _get_account_details(do: SeleniumHelper, account):
    account_type = account["account"]["type"]
    if account_type == "investment":
        return _get_investment_account_details(do, account)
    elif account_type == "cash":
        return _get_cash_account_details(account)
    raise Error(f"unsupported account type {account_type}")


def _iter_accounts(portfolio_table: WebElement):
    for row in portfolio_table.find_elements_by_css_selector("tbody tr"):
        cells = row.find_elements_by_tag_name("td")
        account_name_cell = cells[0].find_element_by_tag_name("a")
        account_summary_url = account_name_cell.get_attribute("href").strip()
        account_name = cells[0].text.strip()
        yield {
            "account": {
                "id": account_name,
                "name": account_name,
                "iso_currency": "GBP",
                "type": _get_account_type(account_name)
            },
            "account_locator": _get_account_locator(account_summary_url),
            "summary_url": account_summary_url,
            "balance": Price.fromstring(cells[1].text.strip()).amount_float
        }


def _get_account_type(account_name):
    if "savings" in account_name.lower():
        return "cash"
    return "investment"


def _get_account_locator(account_url):
    match = re.findall(r"account/(\d+)", account_url)
    if len(match) != 1:
        raise Error(f"unable to find account locator from url {account_url}")
    return match[0]


def _get_accounts_table(do: SeleniumHelper):
    return do.find_maybe(By.CSS_SELECTOR, "table.accounts-table")


def _is_logged_in(do: SeleniumHelper):
    return _get_accounts_table(do) is not None


def _get_online_password_input(do: SeleniumHelper):
    return do.find_maybe(By.ID, "online-password-verification")


def _reached_auth_step2(do: SeleniumHelper):
    return _get_online_password_input(do) is not None


def _get_login_error(do: SeleniumHelper):
    error_area = do.find_maybe(By.CSS_SELECTOR, "div.error-message")
    if error_area:
        return error_area.text.strip()
    field_error_areas = do.find_many(By.CSS_SELECTOR, "label.error")
    if field_error_areas:
        return " ".join(error_area.text.strip()
                        for error_area in field_error_areas)


def _report_auth_error(error_message):
    raise AuthFailure(error_message.replace("\n", " ").strip())
