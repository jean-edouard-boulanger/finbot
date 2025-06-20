import json
from dataclasses import dataclass
from typing import Any, Generator, cast

from playwright.async_api import Locator
from pydantic import SecretStr

from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import raise_
from finbot.providers.errors import AuthenticationError, UnsupportedAccountType
from finbot.providers.playwright_base import (
    Condition,
    ConditionGuard,
    PlaywrightProviderBase,
)
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    Assets,
    AssetsEntry,
)

BASE_URL = "https://www.credit-agricole.fr/{region}/particulier/acceder-a-mes-comptes.html"


class Credentials(BaseModel):
    region: str
    account_number: str
    password: SecretStr


@dataclass(frozen=True)
class AccountValue:
    account: Account
    account_value: float


class Api(PlaywrightProviderBase):
    description = "Credit agricole (FR)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._account_data = None

    def _iter_accounts(self) -> Generator[AccountValue, None, None]:
        def handle_account(data: dict[str, Any]) -> AccountValue:
            account_type, account_sub_type = _parse_account_type_and_subtype(data)
            return AccountValue(
                account=Account(
                    id=data["numeroCompte"].strip(),
                    name=data["libelleProduit"].strip(),
                    iso_currency=data["idDevise"].strip(),
                    type=account_type,
                    sub_type=account_sub_type,
                ),
                account_value=float(data["solde"]),
            )

        assert self._account_data is not None
        yield handle_account(self._account_data["comptePrincipal"])
        for line_item in self._account_data["grandesFamilles"]:
            for account_data in line_item["elementsContrats"]:
                yield handle_account(account_data)

    async def initialize(self) -> None:
        page = self.page
        await page.goto(BASE_URL.format(region=self._credentials.region))
        await ConditionGuard(
            Condition(lambda: page.locator("#loginForm").is_visible()),
            Condition(
                lambda: self.get_element_or_none("div.AemBug-content"),
                when_fulfilled=lambda element: raise_(
                    AuthenticationError(element.inner_text().strip()),
                ),
            ),
        ).wait_any(page)

        # 1. Enter account number

        await page.fill("#Login-account", self._credentials.account_number)
        await page.click("xpath=//button[@login-submit-btn]")
        keypad_locator: Locator = await ConditionGuard(
            Condition(lambda: self.get_element_or_none("#clavier_num")),
        ).wait(page)

        # 2. Type password and validate

        async def keypad_key_is_ready(key_: Locator) -> bool:
            return (await key_.inner_text()).strip().isdigit()

        login_keys_by_num = {}
        for key in await keypad_locator.locator(".Login-key").all():
            await ConditionGuard(Condition(lambda: keypad_key_is_ready(key))).wait(page)
            login_keys_by_num[(await key.inner_text()).strip()] = key
        for digit in self._credentials.password.get_secret_value():
            await login_keys_by_num[digit].click()
        await page.click("#validation")

        await ConditionGuard(
            Condition(lambda: self.get_element_or_none(".Synthesis-user")),
            Condition(
                lambda: self.get_element_or_none("#erreur-keypad"),
                when_fulfilled=lambda el: raise_(
                    AuthenticationError(el.inner_text().strip()),
                ),
            ),
        ).wait_any(page)

        # 2. Get account data

        account_data_str = cast(
            str,
            await page.locator("xpath=//div[@data-ng-controller]").get_attribute("data-ng-init"),
        )[
            len(
                "syntheseController.init("
            ) : -1  # noqa
        ]
        self._account_data = json.loads("[" + account_data_str + "]")[0]

    async def get_accounts(self) -> list[Account]:
        return [entry.account for entry in self._iter_accounts()]

    async def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=entry.account.id,
                    items=[
                        Asset.cash(
                            currency=entry.account.iso_currency,
                            is_domestic=self.user_account_currency == entry.account.iso_currency,
                            amount=entry.account_value,
                        )
                    ],
                )
                for entry in self._iter_accounts()
            ]
        )


def _parse_account_type_and_subtype(account_data: dict[str, Any]) -> tuple[AccountType, str]:
    raw_account_type = account_data["natureCompteBam"].strip()
    if raw_account_type == "CCHQ":
        return AccountType.depository, "checking"
    if raw_account_type in ("LDD", "LEP", "LIV A"):
        return AccountType.depository, "savings"
    raise UnsupportedAccountType(raw_account_type, account_data["libelleProduit"])
