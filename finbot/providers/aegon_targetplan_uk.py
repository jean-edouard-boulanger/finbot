from typing import Any, cast

from playwright.sync_api import Locator, Page
from price_parser import Price  # type: ignore
from pydantic import BaseModel, SecretStr

from finbot.core import schema as core_schema
from finbot.core.utils import raise_
from finbot.providers.errors import AuthenticationFailure
from finbot.providers.playwright_base import (
    Condition,
    ConditionGuard,
    PlaywrightProviderBase,
)
from finbot.providers.schema import (
    Account,
    Asset,
    Assets,
    AssetsEntry,
    BalanceEntry,
    Balances,
)

AUTH_URL = "https://lwp.aegon.co.uk/targetplanUI/login"
BALANCES_URL = "https://lwp.aegon.co.uk/targetplanUI/investments"


class Credentials(BaseModel):
    username: str
    password: SecretStr


class MainDashboardPage(object):
    def __init__(self, page: Page):
        self.page = page
        assert "targetplanUI/investments" in self.page.url

    @staticmethod
    def _extract_account(account_locator: Locator) -> BalanceEntry:
        body_locator = account_locator.locator(".card-body")
        footer_locator = account_locator.locator(".card-footer")
        balance_str = body_locator.locator("span.currency-hero").inner_text().strip()
        return BalanceEntry(
            account=Account(
                id=footer_locator.inner_text().strip().split(" ")[-1],
                name=body_locator.locator("h3").inner_text().strip(),
                iso_currency="GBP",
                type="investment",
            ),
            balance=cast(float, Price.fromstring(balance_str).amount_float),
        )

    def get_accounts(self) -> list[BalanceEntry]:
        account_locators = ConditionGuard(
            Condition(lambda: self.page.locator(".card-product-1").all())
        ).wait()
        return [self._extract_account(locator) for locator in account_locators]


class Api(PlaywrightProviderBase):
    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        self._accounts: list[BalanceEntry] | None = None

    @staticmethod
    def description() -> str:
        return "Aegon Targetplan (UK)"

    @staticmethod
    def create(
        authentication_payload: core_schema.CredentialsPayloadType, **kwargs: Any
    ) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

    def initialize(self) -> None:
        page = self.page
        page.goto(AUTH_URL)
        page.type("input#username", self._credentials.username)
        page.type("input#password", self._credentials.password.get_secret_value())
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

    def get_balances(self) -> Balances:
        return Balances(accounts=cast(list[BalanceEntry], self._accounts))

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account=entry.account,
                    assets=[
                        Asset(
                            name="Generic fund (unknown name)",
                            type="blended fund",
                            value=entry.balance,
                        )
                    ],
                )
                for entry in cast(list[BalanceEntry], self._accounts)
            ]
        )
