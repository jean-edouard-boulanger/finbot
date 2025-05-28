import json
from dataclasses import dataclass
from typing import Any, Generator, cast

from playwright.sync_api import Locator

from finbot.core.pydantic_ import SecretStr
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
SchemaNamespace = "CreditAgricoleProvider"


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

    def initialize(self) -> None:
        page = self.page
        page.goto(BASE_URL.format(region=self._credentials.region))
        ConditionGuard(
            Condition(lambda: page.locator("#loginForm").is_visible()),
            Condition(
                lambda: self.get_element_or_none("div.AemBug-content"),
                when_fulfilled=lambda element: raise_(
                    AuthenticationError(element.inner_text().strip()),
                ),
            ),
        ).wait_any(page)

        # 1. Enter account number

        page.fill("#Login-account", self._credentials.account_number)
        page.click("xpath=//button[@login-submit-btn]")
        keypad_locator: Locator = ConditionGuard(
            Condition(lambda: self.get_element_or_none("#clavier_num")),
        ).wait(page)

        # 2. Type password and validate

        login_keys_by_num = {}
        for key in keypad_locator.locator(".Login-key").all():
            ConditionGuard(Condition(lambda: key.inner_text().strip().isdigit())).wait(page)
            login_keys_by_num[key.inner_text().strip()] = key
        for digit in self._credentials.password.get_secret_value():
            login_keys_by_num[digit].click()
        page.click("#validation")

        ConditionGuard(
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
            page.locator("xpath=//div[@data-ng-controller]").get_attribute("data-ng-init"),
        )[
            len(
                "syntheseController.init("
            ) : -1  # noqa
        ]
        self._account_data = json.loads("[" + account_data_str + "]")[0]

    def get_accounts(self) -> list[Account]:
        return [entry.account for entry in self._iter_accounts()]

    def get_assets(self) -> Assets:
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
