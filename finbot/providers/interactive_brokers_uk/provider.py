import base64
from datetime import datetime
from typing import Any

from pydantic import AwareDatetime, SecretStr

from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.secure import async_pgp_decrypt
from finbot.core.utils import some
from finbot.providers import schema as providers_schema
from finbot.providers.base import ProviderBase
from finbot.providers.errors import UnsupportedFinancialInstrument
from finbot.providers.interactive_brokers_uk.flex_report.parser import (
    parse_flex_report_payload,
)
from finbot.providers.interactive_brokers_uk.flex_report.schema import (
    AccountInformation,
    CashTransaction,
    FlexReport,
    FlexStatement,
    FlexStatementEntries,
    OpenPosition,
    Trade,
    TradeDirection,
)
from finbot.providers.interactive_brokers_uk.intake import (
    IntakeMethod,
    async_load_latest_report_payload,
)
from finbot.providers.schema import Account, AccountType, Transaction, Transactions, TransactionType


class PGPKey(BaseModel):
    data_base64: SecretStr
    passphrase: SecretStr | None = None

    @property
    def pgp_key(self) -> bytes:
        return base64.b64decode(self.data_base64.get_secret_value())


class Credentials(BaseModel):
    report_file_pattern: str = "*.xml"
    intake_method: IntakeMethod
    pgp_key: PGPKey | None


class Api(ProviderBase):
    description = "Interactive Brokers (UK)"
    credentials_type = Credentials

    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        self.__report: FlexReportWrapper | None = None

    async def initialize(self) -> None:
        raw_report_payload = await async_load_latest_report_payload(
            self._credentials.report_file_pattern,
            self._credentials.intake_method,
        )
        if pgp_key := self._credentials.pgp_key:
            report_payload = (
                await async_pgp_decrypt(
                    pgp_key_blob=pgp_key.pgp_key,
                    passphrase=pgp_key.passphrase.get_secret_value() if pgp_key.passphrase else None,
                    encrypted_blob=raw_report_payload,
                )
            ).decode()
        else:
            report_payload = raw_report_payload.decode()
        self.__report = FlexReportWrapper(parse_flex_report_payload(report_payload))

    async def get_accounts(self) -> list[Account]:
        return [statement.account for statement in some(self.__report).statements]

    async def get_assets(self) -> providers_schema.Assets:
        return providers_schema.Assets(
            accounts=[statement.get_assets(self.user_account_currency) for statement in some(self.__report).statements],
        )

    async def get_transactions(self, from_date: AwareDatetime | None = None) -> Transactions:
        all_transactions: list[Transaction] = []
        for statement in some(self.__report).statements:
            all_transactions.extend(statement.get_transactions())
        if from_date:
            all_transactions = [t for t in all_transactions if t.transaction_date >= from_date]
        return Transactions(transactions=all_transactions)


class FlexStatementWrapper:
    def __init__(self, statement: FlexStatement):
        self.statement = statement
        self.account = providers_schema.Account(
            id=self.account_id,
            name=self.account_name,
            iso_currency=self.account_information.currency,
            type=AccountType.investment,
            sub_type="brokerage",
        )

    @property
    def account_id(self) -> str:
        return self.statement.account_id

    @property
    def entries(self) -> FlexStatementEntries:
        return self.statement.entries

    @property
    def account_currency(self) -> CurrencyCode:
        return self.account_information.currency

    @property
    def account_information(self) -> AccountInformation:
        return some(self.entries.account_information)

    @property
    def account_name(self) -> str:
        if self.account_information.alias:
            return f"{self.account_information.alias} ({self.account_id})"
        return self.account_id

    def get_assets(self, user_account_currency: CurrencyCode) -> providers_schema.AssetsEntry:
        cash_assets = [
            providers_schema.Asset.cash(
                currency=entry.currency,
                is_domestic=entry.currency == user_account_currency,
                amount=entry.ending_cash,
            )
            for entry in some(self.entries.cash_report).entries
        ]
        return providers_schema.AssetsEntry(
            account_id=self.account.id,
            items=cash_assets + [_make_asset(entry=entry) for entry in some(self.entries.open_positions).entries],
        )

    def get_transactions(self) -> list[Transaction]:
        transactions: list[Transaction] = []
        if self.entries.trades:
            for trade in self.entries.trades.entries:
                transactions.append(_make_trade_transaction(trade, self.account_id))
        if self.entries.cash_transactions:
            for cash_txn in self.entries.cash_transactions.entries:
                transactions.append(_make_cash_transaction(cash_txn, self.account_id))
        return transactions


class FlexReportWrapper:
    def __init__(self, report: FlexReport):
        self.report = report
        self.statements = [FlexStatementWrapper(entry) for entry in report.statements]


def _make_asset(
    entry: OpenPosition,
) -> providers_schema.Asset:
    asset_category = entry.asset_category
    if asset_category == "STK":
        return providers_schema.Asset(
            name=f"{entry.symbol} - {entry.description}",
            type="equity",
            asset_class=providers_schema.AssetClass.equities,
            asset_type=providers_schema.AssetType.stock,
            value_in_item_ccy=entry.position_value,
            units=entry.position,
            currency=entry.currency,
            isin_code=entry.isin if entry.isin else None,
            provider_specific={
                "Symbol": entry.symbol,
                "Description": entry.description,
                "Side": entry.side.value.lower(),
                entry.security_id_type: entry.security_id,
                "Stock currency": entry.currency,
                "Listing exchange": entry.listing_exchange,
                "Report date": entry.report_date.strftime("%Y-%b-%d"),
            },
        )
    raise UnsupportedFinancialInstrument(asset_category, entry.symbol)


_CASH_TRANSACTION_TYPE_MAP: dict[str, TransactionType] = {
    "Dividends": TransactionType.dividend,
    "Payment In Lieu Of Dividends": TransactionType.dividend,
    "Withholding Tax": TransactionType.tax,
    "Broker Interest Received": TransactionType.interest_earned,
    "Broker Interest Paid": TransactionType.interest_charged,
    "Commission Adjustments": TransactionType.fee,
    "Other Fees": TransactionType.fee,
    "Deposits/Withdrawals": TransactionType.deposit,
}


def _make_trade_transaction(trade: Trade, account_id: str) -> Transaction:
    from datetime import timezone

    txn_type = TransactionType.buy if trade.buy_sell == TradeDirection.buy else TransactionType.sell
    trade_date = trade.trade_time.replace(tzinfo=timezone.utc) if trade.trade_time.tzinfo is None else trade.trade_time
    return Transaction(
        transaction_id=trade.transaction_id,
        account_id=account_id,
        transaction_date=trade_date,
        effective_date=trade_date,
        transaction_type=txn_type,
        amount=trade.net_cash,
        currency=trade.currency,
        description=f"{trade.buy_sell.value.upper()} {abs(trade.quantity)} {trade.symbol} @ {trade.trade_price}",
        symbol=trade.symbol,
        units=abs(trade.quantity),
        unit_price=trade.trade_price,
        fee=abs(trade.ib_commission),
        provider_specific={
            "trade_id": trade.trade_id,
            "exchange": trade.exchange,
            "order_type": trade.order_type,
            "isin": trade.isin,
        },
    )


def _make_cash_transaction(cash_txn: CashTransaction, account_id: str) -> Transaction:
    from datetime import timezone

    txn_type = _CASH_TRANSACTION_TYPE_MAP.get(cash_txn.transaction_type, TransactionType.other)
    if txn_type == TransactionType.deposit and cash_txn.amount < 0:
        txn_type = TransactionType.withdrawal
    cash_date = datetime.combine(cash_txn.settlement_date, datetime.min.time(), tzinfo=timezone.utc)
    return Transaction(
        transaction_id=cash_txn.transaction_id,
        account_id=account_id,
        transaction_date=cash_date,
        effective_date=cash_date,
        transaction_type=txn_type,
        amount=cash_txn.amount,
        currency=cash_txn.currency,
        description=cash_txn.description,
        provider_specific={
            "ib_transaction_type": cash_txn.transaction_type,
        },
    )
