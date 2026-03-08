import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from playwright.async_api import Page, Route
from pydantic import AwareDatetime, SecretStr

from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import now_utc, some
from finbot.providers.errors import AuthenticationError, UnsupportedFinancialInstrument, UnsupportedTransactionType
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
    Transaction,
    Transactions,
    TransactionType,
)

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
        self._lock = asyncio.Lock()

    async def _accounts_payload_is_set(self) -> bool:
        async with self._lock:
            return self._accounts_payload is not None

    async def _handle_contracts_request(self, route: Route, *_: Any) -> None:
        response = await route.fetch()
        await route.fulfill(response=response)
        async with self._lock:
            self._accounts_payload = await response.json()

    async def initialize(self) -> None:
        spy_uri = "**/arkea-rest-endpoint-contract-suravenir/v1.0/suravenir-contracts"
        await self.page.route(spy_uri, self._handle_contracts_request)
        await self.page.goto(BASE_URL)
        await self.page.fill(
            "#_com_liferay_login_web_portlet_LoginPortlet_login", self._credentials.identifier.get_secret_value()
        )
        await self.page.fill(
            "#_com_liferay_login_web_portlet_LoginPortlet_password", self._credentials.password.get_secret_value()
        )
        await self.page.click('button[type="submit"]')
        await ConditionGuard(
            Condition(lambda: self._accounts_payload_is_set()),
            Condition(
                lambda: self.get_element_or_none(".login-container > .alert.alert-danger"),
                when_fulfilled=_handle_auth_error,
            ),
        ).wait_any(self.page)
        await self.page.unroute(spy_uri)

    async def get_accounts(self) -> list[Account]:
        return [_deserialize_account(raw_account) for raw_account in some(self._accounts_payload)["listeContrats"]]

    async def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                await FetchAccountAssets(self.page, raw_account["numeroAdherentContrat"])()
                for raw_account in some(self._accounts_payload)["listeContrats"]
            ]
        )

    async def get_transactions(self, from_date: AwareDatetime | None = None) -> Transactions:
        all_transactions: list[Transaction] = []
        for account in await self.get_accounts():
            account_transactions = [
                transaction
                for transaction in await FetchAccountTransactions(self.page, account)()
                if not from_date or transaction.transaction_date >= from_date
            ]
            all_transactions.extend(account_transactions)
        return Transactions(transactions=all_transactions)


class FetchAccountTransactions:
    def __init__(self, page: Page, account: Account):
        self.page = page
        self._account = account
        self._assets_payload: dict[str, Any] | None = None

    async def __call__(self) -> list[Transaction]:
        logger.debug(f"fetching account '{self._account.id}' transactions")
        await _goto_account(self.page, self._account.id)
        ops_tab = self.page.locator("//a[@href='#/consultation/operations']")
        async with self.page.expect_response(
            lambda r: ("/operation-list/" in r.url) and r.status == 200,
            timeout=30000,
        ) as response_info:
            await ops_tab.click()
        response = await response_info.value
        payload = await response.json()
        return _create_transactions(self._account, payload)


class FetchAccountAssets:
    def __init__(self, page: Page, account_id: str):
        self.page = page
        self._account_id = account_id
        self._assets_payload: dict[str, Any] | None = None
        self._lock = asyncio.Lock()

    async def _handle_assets_request(self, route: Route, *_: Any) -> None:
        response = await route.fetch()
        await route.fulfill(response=response)
        async with self._lock:
            self._assets_payload = await response.json()

    async def _assets_payload_is_set(self) -> bool:
        async with self._lock:
            return self._assets_payload is not None

    async def __call__(self) -> AssetsEntry:
        logger.debug(f"fetching account '{self._account_id}' assets")
        spy_uri = "**/arkea-rest-endpoint-contract-life/v1.0/contract-details/*"
        await self.page.route(spy_uri, self._handle_assets_request)
        await _goto_account(self.page, self._account_id)
        await ConditionGuard(Condition(lambda: self._assets_payload_is_set())).wait_all(self.page)
        await self.page.unroute(spy_uri)
        return AssetsEntry(
            account_id=self._account_id,
            items=[_make_asset(asset_payload) for asset_payload in some(self._assets_payload)["contractSupports"]],
        )


async def _goto_account(
    page: Page,
    account_id: str,
) -> None:
    await page.get_by_role("link", name="Mes contrats").click()
    card_locator = page.locator(f'div.contract:has(:text("{account_id}"))')
    button_locator = card_locator.locator('button[title="Consulter le contrat Suravenir Per"]')
    await button_locator.click()


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
) -> Asset:
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


def _create_transaction(account: Account, payload: Any) -> Transaction | None:
    raw_txn_type = payload["crotypeCode"]
    transaction_date = datetime.fromisoformat(payload["crooperationDate"])
    effective_date = datetime.fromisoformat(payload["effectDate"]) if payload.get("effectDate") else transaction_date
    transaction_type: TransactionType | None
    match raw_txn_type:
        case "671":
            transaction_type = TransactionType.fee
        case "210" | "100":
            transaction_type = TransactionType.deposit
        case "405":
            transaction_type = TransactionType.dividend
        case "620":
            transaction_type = None
        case _:
            raise UnsupportedTransactionType(raw_txn_type, payload["movementLabel"])
    if not transaction_type or effective_date > now_utc():
        return None
    if (state := payload.get("movementState")) and state == "EN_ATTENTE":
        return None
    return Transaction(
        transaction_id=payload["operationId"],
        account_id=account.id,
        transaction_date=transaction_date,
        effective_date=effective_date,
        transaction_type=transaction_type,
        amount=payload["netAmount"],
        currency=account.iso_currency,
        description=payload["movementLabel"],
    )


def _create_transactions(account: Account, payload: Any) -> list[Transaction]:
    return [transaction for raw_txn in payload if (transaction := _create_transaction(account, raw_txn))]


async def _handle_auth_error(error_el: Any) -> None:
    raw = (await error_el.inner_text()).strip()
    message = " ".join(stripped_line for line in raw.splitlines() if (stripped_line := line.strip()))
    message = message.rstrip(".") + "."
    raise AuthenticationError(message)
