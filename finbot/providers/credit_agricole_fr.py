import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Generator
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, SecretStr

from finbot.core.schema import BaseModel, CurrencyCode
from finbot.providers.errors import AuthenticationError, UnsupportedAccountType
from finbot.providers.playwright_base import PlaywrightProviderBase
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    Assets,
    AssetsEntry,
    ProviderSpecificPayloadType,
    Transaction,
    Transactions,
    TransactionType,
)

logger = logging.getLogger(__name__)

# Since the 2026 revamp, the authenticated experience lives on dedicated hosts:
#  - `espace-client.credit-agricole.fr`: the synthesis SPA + its BFF JSON API
#  - `client.ca-connect.credit-agricole.fr`: OAuth2 login
#  - `detail-dav.credit-agricole.fr` / `celc.credit-agricole.fr`: per-account detail
#    micro-frontends (loaded in an iframe) exposing the transactions endpoints.
SPACE_URL = "https://espace-client.credit-agricole.fr/{region}/particulier"
SYNTHESE_URL = "https://espace-client.credit-agricole.fr/{region}/particulier/synthese"
BFF_BASE_URL = "https://espace-client.credit-agricole.fr/bff/api"

# Account "grandes familles" we know how to handle, mapped to a (tab label, transactions
# endpoint marker) pair. The endpoint markers identify the responses to intercept in the
# detail micro-frontend (which lives on a different host loaded inside an iframe).
SUPPORTED_FAMILIES = ("COMPTES", "EPARGNE")
IMPUTEES_MARKER = "/operations/imputees"
EPARGNE_OPERATIONS_MARKER = "/compte_epargne/operations"

# Bounds the number of "load more" interactions per account when collecting transactions.
_MAX_TRANSACTION_PAGES = 25


class Credentials(BaseModel):
    region: str
    account_number: str
    password: SecretStr


@dataclass(frozen=True)
class AccountValue:
    account: Account
    account_value: float
    contract: dict[str, Any]


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
        self._accounts: list[AccountValue] | None = None

    async def initialize(self) -> None:
        await self._login()
        self._accounts = await self._fetch_accounts()

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
        collected: dict[str, Transaction] = {}
        for entry in self._iter_accounts():
            logger.info(f"collecting transactions for account '{entry.account.id}' ({entry.account.name})")
            for transaction in await self._collect_account_transactions(entry, from_date):
                collected[transaction.transaction_id] = transaction
        return Transactions(
            transactions=sorted(
                (t for t in collected.values() if not from_date or t.transaction_date >= from_date),
                key=lambda t: (t.transaction_date, t.transaction_id),
            )
        )

    def _iter_accounts(self) -> Generator[AccountValue, None, None]:
        assert self._accounts is not None
        yield from self._accounts

    async def _login(self) -> None:
        page = self.page
        await page.goto(SPACE_URL.format(region=self._credentials.region))

        # 1. Enter the identifiant (account number) and validate.
        identifiant = page.get_by_role("textbox", name=re.compile("identifiant", re.IGNORECASE))
        try:
            await identifiant.wait_for(state="visible", timeout=30000)
        except Exception as e:
            raise AuthenticationError("could not reach the Credit Agricole login page") from e
        await identifiant.fill(self._credentials.account_number)
        await page.get_by_role("button", name=re.compile("valider", re.IGNORECASE)).click()

        # 2. Solve the secure keypad: each button's accessible name is the digit it
        #    types (the layout is shuffled per session, but the labels are readable).
        try:
            await page.get_by_role("heading", name=re.compile("code personnel", re.IGNORECASE)).wait_for(
                state="visible", timeout=30000
            )
        except Exception as e:
            raise AuthenticationError("invalid identifiant or unexpected login page") from e
        for digit in self._credentials.password.get_secret_value():
            await page.get_by_role("button", name=digit, exact=True).click()
        await page.get_by_role("button", name=re.compile("connecter", re.IGNORECASE)).last.click()

        # 3. The successful login redirects (via OAuth) to the synthesis page.
        try:
            await page.wait_for_url(re.compile(r"/synthese"), timeout=60000)
        except Exception as e:
            raise AuthenticationError("authentication failed (wrong code personnel?)") from e

        await self._dismiss_cookie_banner()

    async def _dismiss_cookie_banner(self) -> None:
        """The synthesis page shows a TrustCommander consent overlay that intercepts
        pointer events until dismissed. Accepting once sets a cookie for the session."""
        overlay = self.page.locator("#privacy-overlay")
        try:
            await overlay.wait_for(state="visible", timeout=4000)
        except Exception:
            return  # no banner (already consented earlier in this session)
        for selector in ("#popin_tc_privacy_button_3", "#popin_tc_privacy_button_2", "#popin_tc_privacy_button"):
            button = self.page.locator(selector)
            try:
                if await button.count() and await button.is_visible():
                    await button.click()
                    await overlay.wait_for(state="hidden", timeout=5000)
                    return
            except Exception:
                continue
        for label in ("Tout accepter", "Tout refuser", "Accepter", "Continuer"):
            button = self.page.get_by_role("button", name=re.compile(label, re.IGNORECASE))
            try:
                if await button.count() and await button.first.is_visible():
                    await button.first.click()
                    await overlay.wait_for(state="hidden", timeout=5000)
                    return
            except Exception:
                continue
        logger.warning("cookie consent overlay present but no known accept button found")

    async def _fetch_accounts(self) -> list[AccountValue]:
        families_query = "&".join(f"code_grande_famille={family}" for family in SUPPORTED_FAMILIES)
        contracts_by_family: dict[str, Any] = await self._bff_get(f"{BFF_BASE_URL}/synthesis/contract?{families_query}")

        accounts: list[AccountValue] = []
        for family in SUPPORTED_FAMILIES:
            contracts = contracts_by_family.get(family) or []
            if not contracts:
                continue
            # Balances come from a separate, per-family endpoint.
            data = await self._bff_get(f"{BFF_BASE_URL}/synthesis/contract/data?code_grande_famille={family}")
            solde_by_account = {
                entry["numero_compte"]: entry["solde"] for entry in (data.get(family) or []) if "solde" in entry
            }
            for contract in contracts:
                account_type, account_sub_type = _parse_account_type_and_subtype(contract)
                accounts.append(
                    AccountValue(
                        account=Account(
                            id=contract["numero_compte"].strip(),
                            name=contract["libelle_produit_commercial"].strip(),
                            iso_currency=contract["code_devise"].strip(),
                            type=account_type,
                            sub_type=account_sub_type,
                        ),
                        account_value=float(solde_by_account.get(contract["numero_compte"], 0.0)),
                        contract=contract,
                    )
                )
        return accounts

    async def _bff_get(self, url: str) -> Any:
        """Fetch a BFF JSON endpoint from within the authenticated page context, so the
        request carries the session cookies and is same-origin."""
        result = await self.page.evaluate(
            """async (url) => {
                const response = await fetch(url, {headers: {accept: 'application/json'}, credentials: 'include'});
                return {status: response.status, body: await response.text()};
            }""",
            url,
        )
        if result["status"] != 200:
            raise RuntimeError(f"unexpected status {result['status']} fetching {url}")
        return json.loads(result["body"])

    async def _collect_account_transactions(
        self,
        entry: AccountValue,
        from_date: AwareDatetime | None,
    ) -> list[Transaction]:
        marker = _transactions_marker(entry.contract)
        captured: list[tuple[str, Any]] = []

        async def on_response(response: Any) -> None:
            if response.status == 200 and marker in response.url:
                try:
                    captured.append((response.url, await response.json()))
                except Exception:
                    pass

        self.page.on("response", on_response)
        try:
            await self._open_account_detail(entry)
            # Wait for the detail micro-frontend to load and fire the first operations call.
            if not await _wait_until(lambda: len(captured) > 0, timeout=30.0):
                logger.warning(f"no transactions response captured for account '{entry.account.id}'")
                return []

            # The detail micro-frontend renders inside an iframe whose id starts with
            # "DETAIL-" (e.g. DETAIL-COMPTE-DAV, DETAIL-EPARGNE); the page also contains a
            # hidden, unrelated helper iframe, so we must not match a bare "iframe".
            frame = self.page.frame_locator("iframe[id^='DETAIL-']")
            # Match the "Afficher plus [d'opérations]" load-more control, but NOT the
            # "Afficher plus de détails" toggle that also sits above the operations list.
            load_more = frame.get_by_text(re.compile(r"afficher plus(?! de détails)", re.IGNORECASE))
            for _ in range(_MAX_TRANSACTION_PAGES):
                if not _needs_more_pages(captured, from_date):
                    break
                try:
                    if not await load_more.first.is_visible(timeout=3000):
                        break
                except Exception:
                    break
                pages_before = len(captured)
                await load_more.first.click()
                # The checking detail only fetches a new page once the buffered rows are
                # exhausted, so an individual click may not trigger a request: just loop.
                await _wait_until(lambda: len(captured) > pages_before, timeout=8.0)
        finally:
            self.page.remove_listener("response", on_response)

        transactions: list[Transaction] = []
        for url, payload in captured:
            if IMPUTEES_MARKER in url:
                transactions.extend(_parse_transactions_from_imputees_response_data(payload, entry.account))
            elif EPARGNE_OPERATIONS_MARKER in url:
                transactions.extend(_parse_transactions_from_operations_response_data(payload, entry.account))
        return transactions

    async def _open_account_detail(self, entry: AccountValue) -> None:
        page = self.page
        await page.goto(SYNTHESE_URL.format(region=self._credentials.region))
        await self._dismiss_cookie_banner()
        tab_name = _account_tab_name(entry.contract)
        await page.get_by_role("tab", name=re.compile(tab_name, re.IGNORECASE)).click()
        await page.get_by_role("link").filter(has_text=entry.account.id).first.click()


def _parse_account_type_and_subtype(contract: dict[str, Any]) -> tuple[AccountType, str]:
    family = contract["code_grande_famille"].strip()
    if family == "COMPTES":
        return AccountType.depository, "checking"
    if family == "EPARGNE":
        return AccountType.depository, "savings"
    raise UnsupportedAccountType(family, contract.get("libelle_produit_commercial", ""))


def _account_tab_name(contract: dict[str, Any]) -> str:
    family = contract["code_grande_famille"].strip()
    return {"COMPTES": "Mes Comptes", "EPARGNE": "Mon Épargne"}[family]


def _transactions_marker(contract: dict[str, Any]) -> str:
    family = contract["code_grande_famille"].strip()
    return IMPUTEES_MARKER if family == "COMPTES" else EPARGNE_OPERATIONS_MARKER


def _scalar_payload(operation: dict[str, Any]) -> ProviderSpecificPayloadType:
    return {k: v for k, v in operation.items() if v is None or isinstance(v, (str, int, float, bool))}


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
            # NOTE: this hashing scheme is kept byte-for-byte identical to the
            # pre-revamp implementation so transaction ids stay stable across the
            # rewrite (the revamped `imputees` payload exposes the same fields). The
            # new per-operation UUID is intentionally NOT used here for that reason;
            # it is still preserved in `provider_specific` (`id`).
            key = {
                "transaction_date": transaction_date.isoformat(),
                "effective_date": effective_date.isoformat(),
                "operation_family": int(operation["codeFamilleOperation"]),
                "operation_subtype": int(operation["codeTypeOperation"]),
                "description": description,
                "amount": f"{amount:.3f}",
                "custom_ref": custom_ref,
                "counterparty": counterparty,
                "warrant_ref": operation["referenceMandat"] or None,
                "creator_id": operation["idEmetteur"],
                "cheque": operation["cheque"],
            }
            hashed_key = hashlib.sha256(json.dumps(key).encode()).hexdigest()
            dates = f"{transaction_date.isoformat()}-{effective_date.isoformat()}"
            transaction_id = f"{account.id}-{dates}-{hashed_key}"
            transactions.append(
                Transaction(
                    transaction_id=transaction_id,
                    account_id=account.id,
                    transaction_date=transaction_date,
                    effective_date=effective_date,
                    transaction_type=_classify_transaction_type(operation),
                    amount=amount,
                    currency=account.iso_currency,
                    description=description,
                    counterparty=counterparty,
                    provider_specific=_scalar_payload(operation),
                )
            )
    return transactions


def _parse_transactions_from_operations_response_data(
    payload: Any,
    account: Account,
) -> list[Transaction]:
    transactions = []
    for operation in payload["operations"]:
        transaction_date = datetime.fromtimestamp(operation["date_operation"] / 1000.0, tz=ZoneInfo("Europe/Paris"))
        effective_date = datetime.fromtimestamp(operation["date_valeur"] / 1000.0, tz=ZoneInfo("Europe/Paris"))
        amount = operation["montant"]
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
                provider_specific=_scalar_payload(operation),
            )
        )
    return transactions


def _newest_first_response_oldest_date(url: str, payload: Any) -> AwareDatetime | None:
    """Oldest transaction date in a single (newest-first) operations response."""
    try:
        if IMPUTEES_MARKER in url:
            blocs = payload.get("operationBlocs") or []
            if not blocs:
                return None
            return _parse_french_date(blocs[-1]["operationDetails"][-1]["dateOperationAffichee"].strip())
        operations = payload.get("operations") or []
        if not operations:
            return None
        return datetime.fromtimestamp(operations[-1]["date_operation"] / 1000.0, tz=ZoneInfo("Europe/Paris"))
    except KeyError, IndexError, ValueError:
        return None


def _response_has_next(payload: Any) -> bool:
    # `imputees` uses `hasNext`, `compte_epargne/operations` uses `has_next`.
    return bool(payload.get("hasNext") or payload.get("has_next"))


def _needs_more_pages(captured: list[tuple[str, Any]], from_date: AwareDatetime | None) -> bool:
    if not captured:
        return True
    url, payload = captured[-1]
    if not _response_has_next(payload):
        return False
    if from_date is not None:
        oldest = _newest_first_response_oldest_date(url, payload)
        if oldest is not None and oldest < from_date:
            return False
    return True


async def _wait_until(predicate: Callable[[], bool], timeout: float, poll: float = 0.25) -> bool:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while True:
        if predicate():
            return True
        if loop.time() >= deadline:
            return False
        await asyncio.sleep(poll)


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
    return datetime(year=int(year), month=month_num, day=int(day), tzinfo=ZoneInfo("Europe/Paris"))


def _classify_transaction_type(raw_txn: Any) -> TransactionType:
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


# Kept for backward compatibility with any external callers / tests.
def _extract_account_number(s: str) -> str | None:
    if m := re.search(r"(\d{11})", s):
        return m.group(1)
    return None
