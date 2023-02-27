import json
from typing import Any, Iterator, cast

from playwright.sync_api import Locator
from pydantic import BaseModel, SecretStr

from finbot import providers
from finbot.core.utils import raise_
from finbot.providers.errors import AuthenticationFailure
from finbot.providers.playwright_based import Condition, ConditionGuard, PlaywrightBased

BASE_URL = (
    "https://www.credit-agricole.fr/{region}/particulier/acceder-a-mes-comptes.html"
)


class Credentials(BaseModel):
    region: str
    account_number: str
    password: SecretStr


class Api(PlaywrightBased):
    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        self._account_data = None

    @staticmethod
    def description() -> str:
        return "Credit agricole (FR)"

    @staticmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

    def _iter_accounts(self) -> Iterator[providers.BalanceEntry]:
        def handle_account(data: dict[str, Any]) -> providers.BalanceEntry:
            return {
                "account": {
                    "id": data["numeroCompte"].strip(),
                    "name": data["libelleUsuelProduit"].strip(),
                    "iso_currency": data["idDevise"].strip(),
                    "type": "cash",
                },
                "balance": data["solde"],
            }

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
                    AuthenticationFailure(element.inner_text().strip())
                ),
            ),
        ).wait_any()

        # 1. Enter account number

        page.fill("#Login-account", self._credentials.account_number)
        page.click("xpath=//button[@login-submit-btn]")
        keypad_locator: Locator = ConditionGuard(
            Condition(lambda: self.get_element_or_none("#clavier_num"))
        ).wait()

        # 2. Type password and validate

        login_keys_by_num = {}
        for key in keypad_locator.locator(".Login-key").all():
            ConditionGuard(Condition(lambda: key.inner_text().strip().isdigit())).wait()
            login_keys_by_num[key.inner_text().strip()] = key
        for digit in self._credentials.password.get_secret_value():
            login_keys_by_num[digit].click()
        page.click("#validation")

        ConditionGuard(
            Condition(lambda: self.get_element_or_none(".Synthesis-user")),
            Condition(
                lambda: self.get_element_or_none("#erreur-keypad"),
                when_fulfilled=lambda el: raise_(
                    AuthenticationFailure(el.inner_text().strip())
                ),
            ),
        ).wait_any()

        # 2. Get account data

        account_data_str = cast(
            str,
            page.locator("xpath=//div[@data-ng-controller]").get_attribute(
                "data-ng-init"
            ),
        )[
            len("syntheseController.init(") : -1  # noqa
        ]
        self._account_data = json.loads("[" + account_data_str + "]")[0]

    def get_balances(self) -> providers.Balances:
        return {
            "accounts": [
                {"account": entry["account"], "balance": entry["balance"]}
                for entry in self._iter_accounts()
            ]
        }

    def get_assets(self) -> providers.Assets:
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "assets": [
                        {"name": "Cash", "type": "currency", "value": entry["balance"]}
                    ],
                }
                for entry in self._iter_accounts()
            ]
        }
