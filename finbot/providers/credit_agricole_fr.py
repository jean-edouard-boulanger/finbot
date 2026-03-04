import asyncio
import json
import logging
import re
import hashlib
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Generator, cast

from playwright.async_api import Locator, Response
from pydantic import AwareDatetime, SecretStr

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
    AssetsEntry, Transactions, Transaction, TransactionType,
)

BASE_URL = "https://www.credit-agricole.fr/{region}/particulier/acceder-a-mes-comptes.html"
DASHBOARD_URL = "https://www.credit-agricole.fr/{region}/particulier/operations/synthese.html"


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
        self._acked_cookie_policy = False

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

    async def get_transactions(self, from_date: AwareDatetime | None = None) -> Transactions:
        accounts_by_id = {account.id: account for account in await self.get_accounts()}
        done_accounts = set()
        collected_transactions = []
        while True:
            await self._goto_dashboard()
            await asyncio.sleep(5.0)
            raw_main_account_id = (await self.page.locator("div.SynthesisMainAccount-headMainDescriptionItem--number").text_content()).strip()
            main_account_id = _extract_account_number(raw_main_account_id)
            main_account = accounts_by_id.get(main_account_id)
            other_account_navs: list[tuple[Account, Locator]] = []
            other_account_links = await self.page.locator("a.npc-sn1-produit-meteo").all()
            for other_account_link in other_account_links:
                if account_number := _extract_account_number(await other_account_link.text_content()):
                    if account := accounts_by_id.get(account_number):
                        other_account_navs.append((account, other_account_link))
            nav, account = None, None
            if main_account_id and main_account and main_account_id not in done_accounts:
                nav, account = self.page.locator("div.SynthesisMainAccount-head"), main_account
            else:
                for other_account, other_account_nav in other_account_navs:
                    if other_account.id not in done_accounts:
                        nav, account = other_account_nav, other_account
                        break
            if not account:
                break
            assert nav
            logging.info(f"collecting transactions for account '{account.id}' ({account.name})")
            async with self.page.expect_response(
                lambda r: ("bff/operations/imputees" in r.url or "bff/api/compte_epargne/operations" in r.url) and r.status == 200,
                timeout=30000,
            ) as response_info:
                await nav.click()
            response = await response_info.value
            collected_transactions.extend(await _parse_transactions(response, account))
            done_accounts.add(account.id)
        return Transactions(
            transactions=sorted(
                (t for t in collected_transactions if not from_date or t.transaction_date >= from_date),
                key=lambda t: t.transaction_date
            )
        )

    async def _goto_dashboard(self):
        await self.page.goto(DASHBOARD_URL.format(region=self._credentials.region))
        if not self._acked_cookie_policy:
            await self.page.click("#popin_tc_privacy_button_3")
            self._acked_cookie_policy = True

def _parse_account_type_and_subtype(account_data: dict[str, Any]) -> tuple[AccountType, str]:
    raw_account_type = account_data["typeProduit"].strip()
    if raw_account_type == "compte":
        return AccountType.depository, "checking"
    if raw_account_type in ("epargne-collecte"):
        return AccountType.depository, "savings"
    raise UnsupportedAccountType(raw_account_type, account_data["libelleProduit"])


def _parse_transactions_from_imputees_response_data(
    payload: Any,
    account: Account,
) -> list[Transaction]:
    transactions = []
    for block in payload["operationBlocs"]:
        for operation in block["operationDetails"]:
            amount = operation["montant"]
            transaction_date = _parse_french_date(operation["dateOperationAffichee"].strip())
            effective_date = _parse_french_date(operation["dateValeurAffichee"].strip())
            description = operation["libelleOperation"]
            custom_ref = operation["referenceClient"].strip() or None
            counterparty = operation["idCreancier"].strip() or None
            if label := operation["libelleComplementaire"]:
                description += f", {label}"
            if label := operation["libelleComplementaire2"]:
                description += f", {label}"
            key = {
                "transaction_date": transaction_date.isoformat(),
                "effective_date": _parse_french_date(operation["dateValeurAffichee"].strip()).isoformat(),
                "operation_family": int(operation["codeFamilleOperation"]),
                "operation_subtype": int(operation["codeTypeOperation"]),
                "description": description,
                "amount": f"{amount:.3f}",
                "custom_ref": custom_ref,
                "counterparty": counterparty,
                "warrant_ref": operation["referenceMandat"] or None,
                "creator_id": operation["idEmetteur"],
                "cheque": operation["cheque"]
            }
            hashed_key = hashlib.sha256(json.dumps(key).encode()).hexdigest()
            transaction_date = _parse_french_date(operation["dateOperationAffichee"].strip())
            transactions.append(
                Transaction(
                    transaction_id=(
                        f"{account.id}"
                        f"-{transaction_date.isoformat()}"
                        f"-{effective_date.isoformat()}"
                        f"-{hashed_key}"
                    ),
                    account_id=account.id,
                    transaction_date=transaction_date,
                    effective_date=effective_date,
                    transaction_type=_classify_transaction_type(operation),
                    amount=amount,
                    currency=account.iso_currency,
                    description=description,
                    counterparty=counterparty,
                    provider_specific=deepcopy(operation),
                )
            )
    return transactions


def _parse_transactions_from_operations_response_data(
    payload: Any,
    account: Account,
) -> list[Transaction]:
    transactions = []
    for operation in payload["operations"]:
        transaction_date = datetime.fromtimestamp(operation['date_operation'] / 1000.0, tz=ZoneInfo("Europe/Paris"))
        effective_date = datetime.fromtimestamp(operation['date_valeur'] / 1000.0, tz=ZoneInfo("Europe/Paris"))
        amount = operation['montant']
        transaction_type = TransactionType.transfer_in if amount > 0 else TransactionType.transfer_out
        if "INTERETS CREDITEURS" in operation["libelle_operation"]:
            transaction_type = TransactionType.interest_earned
        description = operation["libelle_operation"]
        if extra_desc := operation["libelle_complementaire"]:
            description += f", {extra_desc}"
        if extra_desc := operation["libelle_complementaire2"]:
            description += f", {extra_desc}"
        if extra_desc := operation["reference_client"]:
            description += f" ({extra_desc})"
        key = {
            "transaction_date": transaction_date.isoformat(),
            "effective_date": effective_date.isoformat(),
            "description": description,
            "amount": f"{amount:.3f}",
        }
        hashed_key = hashlib.sha256(json.dumps(key).encode()).hexdigest()
        transactions.append(
            Transaction(
                transaction_id=f"{account.id}-{transaction_date.isoformat()}-{effective_date.isoformat()}-{hashed_key}",
                account_id=account.id,
                transaction_date=transaction_date,
                effective_date=effective_date,
                transaction_type=transaction_type,
                amount=amount,
                currency=account.iso_currency,
                description=description,
                provider_specific=deepcopy(operation),
            )
        )
    return transactions


async def _parse_transactions(
    resp: Response,
    account: Account,
) -> list[Transaction]:
    if "bff/operations/imputees" in resp.url:
        return _parse_transactions_from_imputees_response_data(await resp.json(), account)
    elif "bff/api/compte_epargne/operations" in resp.url:
        return _parse_transactions_from_operations_response_data(await resp.json(), account)
    else:
        assert False


def _parse_french_date(s: str) -> AwareDatetime:
    _, day, month, year = s.split()
    if month == "janvier":
        month_num = 1
    elif month.startswith("f"):
        month_num = 2
    elif month == "mars":
        month_num = 3
    elif month == "avril":
        month_num = 4
    elif month == "mai":
        month_num = 5
    elif month == "juin":
        month_num = 6
    elif month == "juillet":
        month_num = 7
    elif month.startswith("ao"):
        month_num = 8
    elif month.startswith("sept"):
        month_num = 9
    elif month.startswith("oct"):
        month_num = 10
    elif month.startswith("nov"):
        month_num = 11
    elif month.startswith("d"):
        month_num = 12
    else:
        assert False
    return cast(AwareDatetime, datetime(year=int(year), month=month_num, day=int(day), tzinfo=ZoneInfo("Europe/Paris")))


def _classify_transaction_type(raw_txn: Any):
    amount = raw_txn["montant"]
    operation_family = int(raw_txn["codeFamilleOperation"])
    operation_subtype = int(raw_txn["codeTypeOperation"])
    match (operation_family, operation_subtype):
        case 6, 26:
            return TransactionType.transfer_out
        case (5, 78) | (12, 67):
            return TransactionType.fee
        case 5 | 11 | 52, _:
            return TransactionType.payment
        case 7 | 12, _:
            return TransactionType.deposit
    return TransactionType.payment if amount < 0 else TransactionType.deposit


def _extract_account_number(s: str) -> str | None:
    if m := re.search(r"(\d{11})", s):
        return m.group(1)
    return None
