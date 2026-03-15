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
    merchant_id: int | None = None
    merchant_name: str | None = None
    merchant_website_url: str | None = None


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


class MonthlySavingsEntry(BaseModel):
    month: str
    income: float
    expenses: float
    savings: float
    savings_rate: float | None
    projected_income: float | None
    projected_expenses: float | None
    projected_savings: float | None
    projected_savings_rate: float | None


class SavingsRateReport(BaseModel):
    valuation_ccy: str
    current_month: MonthlySavingsEntry
    comparison_month: MonthlySavingsEntry


class FilterOption(BaseModel):
    label: str
    value: str
    transaction_count: int


class TransactionFilterOptions(BaseModel):
    accounts: list[FilterOption]
    merchants: list[FilterOption]
    categories: list[FilterOption]
    amount_min: float | None
    amount_max: float | None
    credit_count: int
    debit_count: int
