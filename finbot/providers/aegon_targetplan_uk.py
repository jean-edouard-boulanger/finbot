from typing import Any, cast

from playwright.sync_api import Page, Locator
from price_parser import Price  # type: ignore

from finbot.providers.playwright_based import PlaywrightBased, Condition, ConditionGuard
from finbot.providers.errors import AuthenticationFailure
from finbot import providers
from finbot.core.utils import raise_


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


class MainDashboardPage(object):
    def __init__(self, page: Page):
        self.page = page
        assert "targetplanUI/investments" in self.page.url

    @staticmethod
    def _extract_account(account_locator: Locator) -> providers.BalanceEntry:
        body_locator = account_locator.locator(".card-body")
        footer_locator = account_locator.locator(".card-footer")
        balance_str = body_locator.locator("span.currency-hero").inner_text().strip()
        return {
            "account": {
                "id": footer_locator.inner_text().strip().split(" ")[-1],
                "name": body_locator.locator("h3").inner_text().strip(),
                "iso_currency": "GBP",
                "type": "investment",
            },
            "balance": cast(float, Price.fromstring(balance_str).amount_float),
        }

    def get_accounts(self) -> list[providers.BalanceEntry]:
        account_locators = ConditionGuard(
            Condition(lambda: self.page.locator(".card-product-1").all())
        ).wait_any()
        return [self._extract_account(locator) for locator in account_locators]


class Api(PlaywrightBased):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._accounts: list[providers.BalanceEntry] | None = None

    def initialize(self) -> None:
        self.page.set_default_timeout(60_000)  # Aegon is incredibly slow
        self.page.set_default_navigation_timeout(60_000)  # Aegon is incredibly slow

    def authenticate(self, credentials: Credentials) -> None:
        page = self.page
        page.goto(AUTH_URL)
        page.type("input#username", credentials.username)
        page.type("input#password", credentials.password)
        page.click("#submitButtonAjaxId")
        ConditionGuard(
            Condition(lambda: self.get_element_or_none("a#nav-primary-profile")),
            Condition(
                lambda: self.get_element_or_none("#error-container-wrapper"),
                when_fulfilled=lambda el: raise_(
                    AuthenticationFailure(el.inner_text().strip())
                ),
            ),
        ).wait_any()
        self._accounts = MainDashboardPage(page).get_accounts()

    def get_balances(self) -> providers.Balances:
        return {"accounts": cast(list[providers.BalanceEntry], self._accounts)}

    def get_assets(self) -> providers.Assets:
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "assets": [
                        {
                            "name": "Generic fund (unknown name)",
                            "type": "blended fund",
                            "value": entry["balance"],
                        }
                    ],
                }
                for entry in cast(list[providers.BalanceEntry], self._accounts)
            ]
        }
