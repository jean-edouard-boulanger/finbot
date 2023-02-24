from finbot.providers.playwright_based import PlaywrightBased
from finbot import providers

from typing import Any, Iterator, cast
import json


BASE_URL = (
    "https://www.credit-agricole.fr/{region}/particulier/acceder-a-mes-comptes.html"
)


class Credentials(object):
    def __init__(self, region: str, account_number: str, password: str):
        self.region = region
        self.account_number = account_number
        self.password = password

    @property
    def user_id(self) -> str:
        return self.account_number

    @staticmethod
    def init(data: dict[str, Any]) -> "Credentials":
        return Credentials(data["region"], data["account_number"], data["password"])


class Api(PlaywrightBased):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.account_data = None

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

        assert self.account_data is not None
        yield handle_account(self.account_data["comptePrincipal"])
        for line_item in self.account_data["grandesFamilles"]:
            for account_data in line_item["elementsContrats"]:
                yield handle_account(account_data)

    def authenticate(self, credentials: Credentials) -> None:
        page = self.page
        page.goto(BASE_URL.format(region=credentials.region))
        page.locator("#Login-account").wait_for()

        # 1. Enter account number

        page.fill("#Login-account", credentials.account_number)
        page.click("xpath=//button[@login-submit-btn]")

        # 2. Type password and validate

        login_keys_by_num = {}
        for key in page.locator(".Login-key").all():
            self.wait(lambda: key.inner_text().strip().isdigit())
            login_keys_by_num[key.inner_text().strip()] = key
        for digit in credentials.password:
            login_keys_by_num[digit].click()
        page.click("#validation")
        page.locator(".Synthesis-user")

        # 2. Get account data

        account_data_str = cast(
            str,
            page.locator("xpath=//div[@data-ng-controller]").get_attribute(
                "data-ng-init"
            ),
        )[
            len("syntheseController.init(") : -1  # noqa
        ]
        self.account_data = json.loads("[" + account_data_str + "]")[0]

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
