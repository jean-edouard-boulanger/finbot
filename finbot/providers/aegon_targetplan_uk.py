from finbot.core.utils import swallow_exc
from finbot.providers.selenium_based import SeleniumBased
from finbot.providers.support.selenium import any_of, SeleniumHelper
from finbot.providers.errors import AuthenticationFailure
from finbot import providers

from price_parser import Price  # type: ignore

from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement

from typing import Any, Optional, Iterator
from copy import deepcopy
import logging
import time
import traceback


AUTH_URL = "https://lwp.aegon.co.uk/targetplanUI/login"
BALANCES_URL = "https://lwp.aegon.co.uk/targetplanUI/investments"


class Credentials(object):
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    @property
    def user_id(self) -> str:
        return self.username

    @staticmethod
    def init(data: dict[str, Any]) -> "Credentials":
        return Credentials(data["username"], data["password"])


class Api(SeleniumBased):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.accounts: Optional[dict[str, providers.Account]] = None

    def _go_home(self) -> None:
        (
            self._do.find(By.CSS_SELECTOR, "div#navbarSupportedContent")
            .find_element(By.CSS_SELECTOR, "div.dropdown")
            .find_element(By.TAG_NAME, "a")
            .click()
        )

    def _switch_account(self, account_id: str) -> Any:
        self._go_home()
        accounts_elements = _wait_accounts(self._do)
        for entry in _iter_accounts(accounts_elements):
            if entry["account"]["id"] == account_id:
                retries = 4
                for _ in range(retries):
                    try:
                        time.sleep(2)
                        entry["selenium"]["link_element"].click()

                        self._do.wait_cond(
                            any_of(
                                lambda _: _get_allocations_table(self._do),
                                lambda _: _is_maintenance(self._do.current_url),
                            )
                        )

                        if _is_maintenance(self._do.current_url):
                            logging.warning("Maintenance mode, acknowledging")
                            self._do.find(By.XPATH, "//a[@role='button']").click()
                        return self._do.wait_cond(
                            lambda _: _get_allocations_table(self._do)
                        )
                    except TimeoutException:
                        logging.warning(
                            f"could not go to account page, will try again,"
                            f" trace: {traceback.format_exc()}"
                        )
                    except StaleElementReferenceException:
                        logging.warning(
                            f"stale element, we probably managed to get there after all,"
                            f" trace: {traceback.format_exc()}"
                        )
                        return self._do.wait_cond(
                            lambda _: _get_allocations_table(self._do)
                        )
        raise RuntimeError(f"unknown account {account_id}")

    def authenticate(self, credentials: Credentials) -> None:
        def impl(wait_time: float) -> None:
            self._do.get(AUTH_URL)

            # 1. Enter credentials and submit (after specified time period)

            login_area = self._do.wait_element(By.CSS_SELECTOR, "form#login")
            username_input, password_input = login_area.find_elements(
                By.CSS_SELECTOR, "input.form-control"
            )
            username_input.send_keys(credentials.username)
            password_input.send_keys(credentials.password)
            submit_button = login_area.find_element(By.TAG_NAME, "button")
            time.sleep(wait_time)
            submit_button.click()

            # 2. Wait logged-in or error

            self._do.wait_cond(
                any_of(
                    lambda _: _get_login_error(self._do),
                    lambda _: _is_logged_in(self._do),
                )
            )

            error_message = _get_login_error(self._do)
            if error_message:
                raise AuthenticationFailure(error_message)

            # 3. Get accounts data

            accounts_area = _wait_accounts(self._do)
            self.accounts = {
                entry["account"]["id"]: deepcopy(entry["account"])
                for entry in _iter_accounts(accounts_area)
            }

        submit_wait = 1
        trials = 4
        for i in range(trials):
            try:
                return impl(submit_wait)
            except TimeoutException:
                logging.warning(f"timeout while login, re-trying ({i})")
                submit_wait = submit_wait * 2
                pass
        raise RuntimeError(f"unable to login after {trials} trials")

    def get_balances(self) -> providers.Balances:
        self._go_home()
        accounts_elements = _wait_accounts(self._do)
        return {
            "accounts": [
                {"account": deepcopy(entry["account"]), "balance": entry["balance"]}
                for entry in _iter_accounts(accounts_elements)
            ]
        }

    def get_assets(self) -> providers.Assets:
        def get_account_assets(
            account_id: str, account: providers.Account
        ) -> providers.AssetEntry:
            self._switch_account(account_id)
            assets_table_body = self._do.find(
                By.CSS_SELECTOR, "table.table-invs-allocation > tbody"
            )
            return {
                "account": deepcopy(account),
                "assets": [asset for asset in _iter_assets(assets_table_body)],
            }

        assert self.accounts is not None
        return {
            "accounts": [
                get_account_assets(account_id, account)
                for account_id, account in self.accounts.items()
            ]
        }


@swallow_exc(StaleElementReferenceException)
def _get_login_error(do: SeleniumHelper) -> Optional[str]:
    error_area = do.find_maybe(By.ID, "error-container-wrapper")
    if error_area and error_area.is_displayed():
        error_message: str = error_area.text.strip()
        return error_message
    return None


def _get_allocations_table(do: SeleniumHelper) -> Optional[WebElement]:
    return do.find_maybe(By.CSS_SELECTOR, "table.table-invs-allocation")


def _is_maintenance(current_url: str) -> bool:
    return "maintenance" in current_url


def _is_logged_in(do: SeleniumHelper) -> bool:
    avatar_area = do.find_maybe(By.CSS_SELECTOR, "a#nav-primary-profile")
    return avatar_area is not None


def _wait_accounts(do: SeleniumHelper) -> list[WebElement]:
    accounts_xpath = "//div[contains(@class,'card-product-')]"
    do.wait_element(By.XPATH, accounts_xpath, timeout=120)
    return do.find_many(By.XPATH, accounts_xpath)


def _iter_accounts(accounts_elements: list[WebElement]) -> list[dict[str, Any]]:
    def extract_account(account_card: WebElement) -> dict[str, Any]:
        card_body = account_card.find_element(By.CSS_SELECTOR, "div.card-body")
        card_footer = account_card.find_element(By.CSS_SELECTOR, "div.card-footer")
        account_id = card_footer.text.strip().split(" ")[-1]
        account_link = card_body.find_element(By.TAG_NAME, "h3").find_element(
            By.CSS_SELECTOR, "a.view-manage-btn"
        )
        account_name = account_link.text.strip()
        balance_str = card_body.find_element(
            By.CSS_SELECTOR, "div.h1 > span.currency-hero"
        ).text.strip()
        return {
            "account": {
                "id": account_id,
                "name": account_name,
                "iso_currency": "GBP",
                "type": "investment",
            },
            "balance": Price.fromstring(balance_str).amount_float,
            "selenium": {"ref": account_card, "link_element": account_link},
        }

    return [extract_account(account_card) for account_card in accounts_elements]


def _iter_assets(assets_table_body: WebElement) -> Iterator[providers.Asset]:
    for row in assets_table_body.find_elements(By.TAG_NAME, "tr"):
        cells = row.find_elements(By.TAG_NAME, "td")
        asset_name = (
            cells[0]
            .find_element(By.TAG_NAME, "a")
            .find_elements(By.TAG_NAME, "span")[1]
            .text.strip()
        )
        yield {
            "name": asset_name,
            "type": "blended fund",
            "units": float(cells[1].text.strip()),
            "value": float(cells[3].text.strip()),
            "provider_specific": {"Last price": float(cells[2].text.strip())},
        }
