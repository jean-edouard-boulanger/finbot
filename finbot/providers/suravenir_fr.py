import json
import logging
from dataclasses import dataclass
from threading import Lock
from typing import Any

from playwright.sync_api import Route

from finbot.core.pydantic_ import SecretStr
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import raise_, some
from finbot.providers.errors import AuthenticationError
from finbot.providers.playwright_base import (
    Condition,
    ConditionGuard,
    PlaywrightProviderBase,
)
from finbot.providers.schema import Account, AccountType, Asset, AssetClass, Assets, AssetsEntry, AssetType

BASE_URL = "https://espaceclient.suravenir.fr/web/suravenir"


logger = logging.getLogger(__name__)


class Credentials(BaseModel):
    identifier: SecretStr
    password: SecretStr


@dataclass(frozen=True)
class AccountValue:
    account: Account
    account_value: float


class Api(PlaywrightProviderBase):
    description = "Suravenir"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._accounts_payload: dict[str, Any] | None = None
        self._lock = Lock()

    def _accounts_payload_is_set(self) -> bool:
        with self._lock:
            return self._accounts_payload is not None

    def _handle_request(self, route: Route, *_: Any) -> None:
        response = route.fetch()
        route.fulfill(response=response)
        with self._lock:
            self._accounts_payload = response.json()

    def initialize(self) -> None:
        self.page.route("**/arkea-rest-endpoint-contract-suravenir/v1.0/suravenir-contracts", self._handle_request)
        self.page.goto(BASE_URL)
        self.page.fill(
            "#_com_liferay_login_web_portlet_LoginPortlet_login", self._credentials.identifier.get_secret_value()
        )
        self.page.fill(
            "#_com_liferay_login_web_portlet_LoginPortlet_password", self._credentials.password.get_secret_value()
        )
        self.page.click('button[type="submit"]')
        ConditionGuard(
            Condition(lambda: self._accounts_payload_is_set()),
            Condition(
                lambda: self.get_element_or_none(".login-container > .alert.alert-danger"),
                when_fulfilled=lambda element: raise_(
                    AuthenticationError(_format_auth_error(element.inner_text().strip())),
                ),
            ),
        ).wait_any(self.page)
        print(json.dumps(self._accounts_payload, indent=3))

    def get_accounts(self) -> list[Account]:
        return [_deserialize_account(raw_account) for raw_account in some(self._accounts_payload)["listeContrats"]]

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=raw_account["numeroAdherentContrat"],
                    items=[
                        Asset(
                            name="Generic fund (unknown name)",
                            type="blended fund",
                            asset_class=AssetClass.multi_asset,
                            asset_type=AssetType.generic_fund,
                            currency=CurrencyCode("EUR"),
                            value_in_account_ccy=raw_account["soldeContrat"],
                        )
                    ],
                )
                for raw_account in some(self._accounts_payload)["listeContrats"]
            ]
        )


def _format_auth_error(raw: str) -> str:
    message = " ".join(stripped_line for line in raw.splitlines() if (stripped_line := line.strip()))
    message = message.rstrip(".") + "."
    return message


def _deserialize_account(raw_account: Any) -> Account:
    return Account(
        id=raw_account["numeroAdherentContrat"],
        name=raw_account["produit"]["libelleLongProduit"],
        iso_currency=CurrencyCode("EUR"),
        type=AccountType.investment,
        sub_type="pension",
    )
