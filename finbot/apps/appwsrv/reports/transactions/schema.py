from pydantic import AwareDatetime

from finbot.core.schema import BaseModel


class TransactionEntry(BaseModel):
    id: int
    linked_account_id: int
    linked_account_name: str
    sub_account_id: str
    sub_account_name: str
    transaction_date: AwareDatetime
    transaction_type: str
    amount: float
    amount_snapshot_ccy: float | None
    currency: str
    description: str
    symbol: str | None
    units: float | None
    unit_price: float | None
    fee: float | None
    counterparty: str | None
    spending_category_primary: str | None
    spending_category_detailed: str | None
    matched_transaction_id: int | None


class TransactionsReport(BaseModel):
    valuation_ccy: str
    transactions: list[TransactionEntry]
    total_count: int


class CashFlowCategoryEntry(BaseModel):
    transaction_type: str
    total: float


class CashFlowSummary(BaseModel):
    valuation_ccy: str
    from_date: AwareDatetime
    to_date: AwareDatetime
    net_cash_flow: float
    by_category: list[CashFlowCategoryEntry]


class CashFlowTimeSeriesEntry(BaseModel):
    period: str
    inflows: float
    outflows: float
    net: float


class CashFlowTimeSeries(BaseModel):
    valuation_ccy: str
    entries: list[CashFlowTimeSeriesEntry]


class SpendingBreakdownEntry(BaseModel):
    category: str
    total: float
    transaction_count: int


class SpendingBreakdown(BaseModel):
    valuation_ccy: str
    from_date: AwareDatetime
    to_date: AwareDatetime
    entries: list[SpendingBreakdownEntry]
