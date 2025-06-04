import logging
from dataclasses import dataclass
from threading import Lock
from typing import Any

from playwright.sync_api import Page, Route
from pydantic import SecretStr

from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import raise_, some
from finbot.providers.errors import AuthenticationError, UnsupportedFinancialInstrument
from finbot.providers.playwright_base import (
    Condition,
    ConditionGuard,
    PlaywrightProviderBase,
)
from finbot.providers.schema import Account, AccountType, Asset, AssetClass, Assets, AssetsEntry, AssetType

BASE_URL = "https://espaceclient.suravenir.fr/web/suravenir"
ACCOUNTS_URL = "https://espaceclient.suravenir.fr/mes-contrats#/"

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

    def _handle_contracts_request(self, route: Route, *_: Any) -> None:
        response = route.fetch()
        route.fulfill(response=response)
        with self._lock:
            self._accounts_payload = response.json()

    def initialize(self) -> None:
        spy_uri = "**/arkea-rest-endpoint-contract-suravenir/v1.0/suravenir-contracts"
        self.page.route(spy_uri, self._handle_contracts_request)
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
        self.page.unroute(spy_uri)

    def get_accounts(self) -> list[Account]:
        return [_deserialize_account(raw_account) for raw_account in some(self._accounts_payload)["listeContrats"]]

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                FetchAccountAssets(self.page, raw_account["numeroAdherentContrat"])()
                for raw_account in some(self._accounts_payload)["listeContrats"]
            ]
        )


class FetchAccountAssets:
    def __init__(self, page: Page, account_id: str):
        self.page = page
        self._account_id = account_id
        self._assets_payload: dict[str, Any] | None = None
        self._lock = Lock()

    def _handle_assets_request(self, route: Route, *_: Any) -> None:
        response = route.fetch()
        route.fulfill(response=response)
        with self._lock:
            self._assets_payload = response.json()

    def _assets_payload_is_set(self) -> bool:
        with self._lock:
            return self._assets_payload is not None

    def __call__(self) -> AssetsEntry:
        logger.debug(f"Fetching account '{self._account_id}' assets")
        spy_uri = "**/arkea-rest-endpoint-contract-life/v1.0/contract-details/*"
        self.page.route(spy_uri, self._handle_assets_request)
        self.page.goto(ACCOUNTS_URL)
        card_locator = self.page.locator(f'div.contract:has(:text("{self._account_id}"))')
        button_locator = card_locator.locator('button[title="Consulter le contrat Suravenir Per"]')
        button_locator.click()
        ConditionGuard(Condition(lambda: self._assets_payload_is_set())).wait_all(self.page)
        self.page.unroute(spy_uri)
        return AssetsEntry(
            account_id=self._account_id,
            items=[_make_asset(asset_payload) for asset_payload in self._assets_payload["contractSupports"]],
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


def _make_asset(
    asset_payload: dict[str, Any],
):
    if asset_payload["supportCategoryCode"] in ("ET",):  # Electronically traded?
        return Asset(
            name=asset_payload["supportLabel"],
            asset_class={"ACTIONS INTL - GENERAL": AssetClass.equities}[asset_payload["supportClassificationLabel"]],
            asset_type=AssetType.ETF,
            value_in_account_ccy=asset_payload["grossBalance"],
            units=asset_payload["shareCount"],
            currency=CurrencyCode("EUR"),
            isin_code=asset_payload["isinCode"],
            provider_specific={
                "Performance (%)": asset_payload["performance"],
                "Valuation Date": asset_payload["lastNetAssetValue"],
                "Management Fee": asset_payload["managementFee"],
                "Unit Cost Price": asset_payload["unitCostPrice"],
            },
        )
    raise UnsupportedFinancialInstrument(
        asset_type=f"{asset_payload['supportLabel']} - {asset_payload['supportClassificationLabel']}",
        asset_description=f"{asset_payload.get('supportLabel')}",
    )
