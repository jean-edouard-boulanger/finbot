from dataclasses import dataclass
from typing import Any, Optional

from pydantic import SecretStr, AwareDatetime

from finbot.core import qonto_api
from finbot.core.qonto_api import QontoApi, Unauthorized
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import some
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    Assets,
    AssetsEntry, Transactions, Transaction, TransactionType,
)

AUTH_URL = "https://app.qonto.com/signin"


class Credentials(BaseModel):
    identifier: str
    secret_key: SecretStr


@dataclass(frozen=True)
class AccountValue:
    account: Account
    account_value: float


class Api(ProviderBase):
    description = "Qonto (US)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._api: QontoApi | None = None
        self._accounts: Optional[list[AccountValue]] = None

    async def initialize(self) -> None:
        self._api = QontoApi(
            identifier=self._credentials.identifier,
            secret_key=self._credentials.secret_key.get_secret_value(),
        )
        try:
            organization = (await self._api.list_organizations())[0]
        except Unauthorized as e:
            raise AuthenticationError(str(e)) from e
        self._accounts = [
            AccountValue(
                account=Account(
                    id=entry.slug,
                    name=entry.name,
                    iso_currency=CurrencyCode(entry.currency),
                    type=AccountType.depository,
                    sub_type="checking",
                ),
                account_value=entry.balance,
            )
            for entry in organization.bank_accounts
        ]

    async def get_accounts(self) -> list[Account]:
        return [entry.account for entry in some(self._accounts)]

    async def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=entry.account.id,
                    items=[
                        Asset.cash(
                            currency=entry.account.iso_currency,
                            is_domestic=entry.account.iso_currency == self.user_account_currency,
                            amount=entry.account_value,
                        )
                    ],
                )
                for entry in some(self._accounts)
            ]
        )

    async def get_transactions(self, from_date: AwareDatetime | None = None) -> Transactions:
        organization = (await self._api.list_organizations())[0]
        all_transactions = []
        for bank_account in organization.bank_accounts:
            account_transactions: list[qonto_api.Transaction] = await self._api.list_transactions(bank_account.iban, from_date)
            all_transactions.extend(
                Transaction(
                    transaction_id=txn.transaction_id,
                    account_id=bank_account.slug,
                    transaction_date=txn.emitted_at,
                    effective_date=txn.settled_at,
                    transaction_type=get_transaction_type(txn.side, txn.category),
                    amount=-1.0 * txn.amount if txn.side == 'debit' else txn.amount,
                    currency=CurrencyCode(txn.currency),
                    description=_make_transaction_description(txn),
                )
                for txn in account_transactions
            )
        return Transactions(transactions=all_transactions)


def _make_transaction_description(txn: qonto_api.Transaction):
    description = txn.label
    if txn.reference:
        description += f" - {txn.reference}"
    return description


# Maps (side, category) -> TransactionType
_MAPPING: dict[tuple[str, str], TransactionType] = {
    # ── Credits ──────────────────────────────────────────────────────────────
    ("credit", "other_income"):       TransactionType.deposit,
    ("credit", "sales"):              TransactionType.deposit,
    ("credit", "refund"):             TransactionType.adjustment,
    # Money received from another account owned by the same person
    ("credit", "treasury_and_interco"): TransactionType.transfer_in,

    # ── Debits ───────────────────────────────────────────────────────────────
    # Wage transfers to the owner (sole trader paying themselves)
    ("debit", "salary"):              TransactionType.transfer_out,

    # Bank / platform fees
    ("debit", "fees"):                TransactionType.fee,
    ("debit", "subscription"):        TransactionType.fee,

    # Social-security contributions (URSSAF) and government taxes (CFE)
    ("debit", "other_expense"):       TransactionType.tax,
    ("debit", "tax"):                 TransactionType.tax,
    ("debit", "other_service"):       TransactionType.tax,

    # Card spending on goods / services
    ("debit", "marketing"):           TransactionType.purchase,
    ("debit", "online_service"):      TransactionType.purchase,
    ("debit", "hardware_and_equipment"): TransactionType.purchase,

    # Generic outflows that don't fit a narrower bucket
    ("debit", "other"):               TransactionType.payment,
}


def get_transaction_type(side: str, category: str | None) -> TransactionType:
    """
    Map a Qonto (side, category) pair to a TransactionType.

    Parameters
    ----------
    side     : "credit" or "debit"
    category : the category string from the transaction payload

    Returns
    -------
    The matching TransactionType, or TransactionType.other if unknown.
    """
    default = TransactionType.withdrawal if side == 'debit' else TransactionType.deposit
    if not category:
        return default
    key = (side.lower(), category.lower())
    return _MAPPING.get(key, default)
