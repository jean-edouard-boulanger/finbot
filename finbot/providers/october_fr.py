from finbot.core.utils import unwrap_optional
from finbot.providers.errors import AuthenticationFailure
from finbot.providers.selenium_based import SeleniumBased
from finbot.providers.support.selenium import SeleniumHelper
from finbot import providers

from forex_python.converter import get_currency_code_from_symbol

from price_parser import Price  # type: ignore

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from typing import Any, Optional

AUTH_URL = "https://app.october.eu/login"


class Credentials(object):
    def __init__(self, username: str, password: str):
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
        self._capitals: Optional[dict[str, Any]] = None

    def _get_account(self) -> providers.Account:
        capitals = unwrap_optional(self._capitals)
        return {
            "id": "portfolio",
            "name": "Portfolio",
            "iso_currency": capitals["currency_code"],
            "type": "lending",
        }

    def authenticate(self, credentials: Credentials) -> None:
        self.browser.get(AUTH_URL)
        form_elem = self._do.wait_element(By.TAG_NAME, "form")
        email_elem = form_elem.find_element(By.NAME, "email")
        password_elem = form_elem.find_element(By.NAME, "password")
        email_elem.send_keys(credentials.username)
        password_elem.send_keys(credentials.password)
        footer_elem = self._do.wait_element(By.TAG_NAME, "footer")
        auth_button = footer_elem.find_element(By.TAG_NAME, "button")
        auth_button.click()
        _get_portfolio_nav_elem(self._do)

        self._do.assert_success(_is_logged_in, _get_login_error, _report_auth_error)

        portfolio_nav_elem = _get_portfolio_nav_elem(self._do)
        assert portfolio_nav_elem is not None
        self._do.click(portfolio_nav_elem)
        self._capitals = _extract_capitals(self._do)

    def get_balances(self) -> providers.Balances:
        capitals = unwrap_optional(self._capitals)
        balance = capitals["outstanding_balance"] + capitals["available_balance"]
        return {"accounts": [{"account": self._get_account(), "balance": balance}]}

    def get_assets(self) -> providers.Assets:
        capitals = unwrap_optional(self._capitals)
        return {
            "accounts": [
                {
                    "account": self._get_account(),
                    "assets": [
                        {
                            "name": "Cash",
                            "type": "currency",
                            "value": capitals["available_balance"],
                        },
                        {
                            "name": "Loans",
                            "type": "loan",
                            "value": capitals["outstanding_balance"],
                        },
                    ],
                }
            ]
        }


def _get_portfolio_nav_elem(do: SeleniumHelper) -> Optional[WebElement]:
    return do.find_maybe(By.XPATH, "//a[@href='/transactions/summary']")


def _is_logged_in(do: SeleniumHelper) -> bool:
    return _get_portfolio_nav_elem(do) is not None


def _get_login_error(do: SeleniumHelper) -> Optional[str]:
    error_elem = do.find_maybe(By.CSS_SELECTOR, "p.error")
    if error_elem:
        error_message: str = error_elem.text.strip()
        return error_message
    return None


def _extract_capitals(do: SeleniumHelper) -> dict[str, Any]:
    synthesis_elem = do.wait_element(By.XPATH, "//article[text()='October Synthesis']")
    raw_capitals = synthesis_elem.find_element(By.TAG_NAME, "p").text.strip()
    raw_outstanding, raw_available = raw_capitals.split("/")
    outstanding = Price.fromstring(raw_outstanding)
    available = Price.fromstring(raw_available)
    return {
        "outstanding_balance": unwrap_optional(outstanding.amount_float),
        "available_balance": unwrap_optional(available.amount_float),
        "currency_code": get_currency_code_from_symbol(
            unwrap_optional(outstanding.currency)
        ),
    }


def _report_auth_error(error_message: str) -> None:
    raise AuthenticationFailure(error_message.replace("\n", " ").strip())
