from dataclasses import dataclass
from typing import Any, cast

from playwright.sync_api import Locator, Page
from price_parser import Price  # type: ignore

from finbot.core.pydantic_ import SecretStr
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import raise_, some
from finbot.providers.errors import AuthenticationError
from finbot.providers.playwright_base import (
    Condition,
    ConditionGuard,
    PlaywrightProviderBase,
)
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    AssetClass,
    Assets,
    AssetsEntry,
    AssetType,
)

AUTH_URL = "https://lwp.aegon.co.uk/targetplanUI/login"
BALANCES_URL = "https://lwp.aegon.co.uk/targetplanUI/investments"
SchemaNamespace = "AegonProvider"


class AegonTargetplanCredentials(BaseModel):
    username: str
    password: SecretStr


@dataclass(frozen=True)
class AccountValue:
    account: Account
    account_value: float


class MainDashboardPage(object):
    def __init__(self, page: Page):
        self.page = page
        assert "targetplanUI/investments" in self.page.url

    @staticmethod
    def _extract_account(account_locator: Locator) -> AccountValue:
        body_locator = account_locator.locator(".card-body")
        footer_locator = account_locator.locator(".card-footer")
        balance_str = body_locator.locator("span.currency-hero").inner_text().strip()
        return AccountValue(
            account=Account(
                id=footer_locator.inner_text().strip().split(" ")[-1],
                name=body_locator.locator("h3").inner_text().strip(),
                iso_currency=CurrencyCode("GBP"),
                type=AccountType.investment,
                sub_type="pension",
            ),
            account_value=cast(float, Price.fromstring(balance_str).amount_float),
        )

    def get_accounts(self) -> list[AccountValue]:
        account_locators = ConditionGuard(
            Condition(lambda: self.page.locator(".card-product-1").all()),
        ).wait(self.page)
        return [self._extract_account(locator) for locator in account_locators]


class Api(PlaywrightProviderBase):
    description = "Aegon Targetplan (UK)"
    credentials_type = AegonTargetplanCredentials

    def __init__(
        self,
        credentials: AegonTargetplanCredentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._accounts: list[AccountValue] | None = None

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
                    AuthenticationError(el.inner_text().strip()),
                ),
            ),
        ).wait_any(page)
        self._accounts = MainDashboardPage(page).get_accounts()

    def get_accounts(self) -> list[Account]:
        return [entry.account for entry in some(self._accounts)]

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=entry.account.id,
                    items=[
                        Asset(
                            name="Generic fund (unknown name)",
                            type="blended fund",
                            asset_class=AssetClass.multi_asset,
                            asset_type=AssetType.generic_fund,
                            currency=entry.account.iso_currency,
                            value_in_account_ccy=entry.account_value,
                        )
                    ],
                )
                for entry in some(self._accounts)
            ]
        )
