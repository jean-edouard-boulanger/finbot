from finbot.providers.selenium_based import SeleniumBased
from finbot.providers.support.selenium import SeleniumHelper
from finbot.providers.errors import AuthFailure
from finbot import providers

from price_parser import Price  # type: ignore
from forex_python.converter import get_currency_code_from_symbol

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from typing import Any, Optional
from copy import deepcopy


AUTH_URL = "https://app.qonto.com/signin"


class Credentials(object):
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

    @property
    def user_id(self) -> str:
        return self.email

    @staticmethod
    def init(data: dict[str, Any]) -> "Credentials":
        return Credentials(data["email"], data["password"])


class Api(SeleniumBased):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.accounts: Optional[providers.Balances] = None

    def authenticate(self, credentials: Credentials) -> None:
        self._do.get(AUTH_URL)
        form_elem = self._do.wait_element(By.TAG_NAME, "form")
        email_elem: WebElement
        password_elem: WebElement
        email_elem, password_elem = form_elem.find_elements(By.TAG_NAME, "input")
        email_elem.send_keys(credentials.email)
        password_elem.send_keys(credentials.password)
        button = form_elem.find_element(By.TAG_NAME, "button")
        button.click()

        self._do.assert_success(
            lambda _: self._do.find_maybe(
                By.CSS_SELECTOR, "div.l-app-content__page-header"
            ),
            _get_login_error,
            on_failure=_report_auth_error,
        )

        self.accounts = _get_accounts(
            self._do.find(By.CSS_SELECTOR, "div.l-app-content__page-header")
        )

    def get_balances(self) -> providers.Balances:
        assert self.accounts is not None
        return deepcopy(self.accounts)

    def get_assets(self) -> providers.Assets:
        assert self.accounts is not None
        return {
            "accounts": [
                {
                    "account": deepcopy(entry["account"]),
                    "assets": [
                        {"name": "Cash", "type": "currency", "value": entry["balance"]}
                    ],
                }
                for entry in self.accounts["accounts"]
            ]
        }


def _get_accounts(header_elem: WebElement) -> providers.Balances:
    raw_balance = header_elem.find_element(By.CSS_SELECTOR, "h1.title-1").text.strip()
    price = Price.fromstring(raw_balance)
    amount, symbol = price.amount_float, price.currency
    assert amount is not None
    assert symbol is not None
    currency_code = get_currency_code_from_symbol(symbol)
    assert currency_code is not None
    return {
        "accounts": [
            {
                "account": {
                    "id": "main_account",
                    "name": "Main account",
                    "iso_currency": currency_code,
                    "type": "cash",
                },
                "balance": amount,
            }
        ]
    }


def _get_login_error(do: SeleniumHelper) -> Optional[str]:
    error_elem = do.find_maybe(By.CSS_SELECTOR, "div.x-error__message")
    if error_elem and error_elem.is_displayed():
        error_message: str = error_elem.text.replace("\n", " ").strip()
        return error_message
    return None


def _report_auth_error(error_message: str) -> None:
    raise AuthFailure(error_message)
