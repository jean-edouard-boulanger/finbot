from dataclasses import dataclass
from typing import Any, cast

from playwright.sync_api import Page, Locator
from price_parser import Price  # type: ignore

from finbot.providers.playwright_based import PlaywrightBased, PlaywrightHelper
from finbot import providers


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


@dataclass
class AccountDescriptor:
    account_id: str
    name: str
    balance: float


class MainDashboardPage(PlaywrightHelper):
    def __init__(self, page: Page):
        self.page = page

    def _goto_dashboard_if_needed(self) -> None:
        if "targetplanUI/investments" not in self.page.url:
            self.page.locator(".navbar").locator(".header-logo").click()

    @staticmethod
    def _extract_account(account_locator: Locator) -> AccountDescriptor:
        body_locator = account_locator.locator(".card-body")
        footer_locator = account_locator.locator(".card-footer")
        balance_str = body_locator.locator("span.currency-hero").inner_text().strip()
        return AccountDescriptor(
            account_id=footer_locator.inner_text().strip().split(" ")[-1],
            name=body_locator.locator("h3").inner_text().strip(),
            balance=cast(float, Price.fromstring(balance_str).amount_float),
        )

    def get_accounts(self) -> list[AccountDescriptor]:
        self._goto_dashboard_if_needed()
        account_locators = self.wait(lambda: self.page.locator(".card-product-1").all())
        return [self._extract_account(locator) for locator in account_locators]


class Api(PlaywrightBased):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._accounts: list[AccountDescriptor] | None = None

    def initialize(self) -> None:
        self.page.set_default_timeout(60_000)  # Aegon is incredibly slow
        self.page.set_default_navigation_timeout(60_000)  # Aegon is incredibly slow

    def authenticate(self, credentials: Credentials) -> None:
        page = self.page
        page.goto(AUTH_URL)
        page.type("input#username", credentials.username)
        page.type("input#password", credentials.password)
        page.click("#submitButtonAjaxId")
        page.locator("a#nav-primary-profile").wait_for()
        self._accounts = MainDashboardPage(page).get_accounts()

    def get_balances(self) -> providers.Balances:
        return {
            "accounts": [
                {
                    "account": {
                        "id": entry.account_id,
                        "name": entry.name,
                        "iso_currency": "GBP",
                        "type": "investment",
                    },
                    "balance": entry.balance,
                }
                for entry in cast(list[AccountDescriptor], self._accounts)
            ]
        }

    def get_assets(self) -> providers.Assets:
        return {
            "accounts": [
                {
                    "account": {
                        "id": entry.account_id,
                        "name": entry.name,
                        "iso_currency": "GBP",
                        "type": "investment",
                    },
                    "assets": [
                        {
                            "name": "Generic fund (unknown name)",
                            "type": "blended fund",
                            "value": entry.balance,
                        }
                    ],
                }
                for entry in cast(list[AccountDescriptor], self._accounts)
            ]
        }
