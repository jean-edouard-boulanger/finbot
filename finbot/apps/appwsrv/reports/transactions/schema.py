from datetime import date
from typing import Any

from pydantic import AwareDatetime

from finbot.core.schema import BaseModel


class MerchantDetail(BaseModel):
    id: int
    name: str
    description: str | None
    category: str | None
    website_url: str | None


class RecurringGroupDetail(BaseModel):
    id: int
    currency: str
    avg_amount: float
    avg_interval_days: float
    transaction_count: int
    total_spent: float
    total_spent_ccy: float | None
    yearly_cost: float
    first_seen: AwareDatetime
    last_seen: AwareDatetime
    description: str | None = None


class MatchDetail(BaseModel):
    match_confidence: float
    match_status: str
    counterpart_transaction_id: int
    counterpart_account_name: str
    counterpart_description: str
    counterpart_amount: float
    counterpart_currency: str


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
    recurring_group_id: int | None = None


class TransactionDetail(BaseModel):
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
    spending_category_source: str | None
    provider_specific_data: dict[str, Any] | None
    merchant: MerchantDetail | None = None
    recurring_group: RecurringGroupDetail | None = None
    match: MatchDetail | None = None


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


class SubscriptionEntry(BaseModel):
    id: int
    merchant_name: str
    description: str | None
    currency: str
    avg_amount: float
    avg_interval_days: float
    yearly_cost: float
    total_spent_this_year: float
    last_seen: AwareDatetime
    first_seen: AwareDatetime
    transaction_count: int


class SubscriptionsReport(BaseModel):
    valuation_ccy: str
    estimated_yearly_total: float
    total_spent_this_year: float
    subscriptions: list[SubscriptionEntry]


class SpendingCalendarRecurringPayment(BaseModel):
    subscription_id: int
    merchant_name: str
    description: str | None
    currency: str
    avg_amount: float
    is_projected: bool


class SpendingCalendarDay(BaseModel):
    date: date
    total_spending: float
    recurring_payments: list[SpendingCalendarRecurringPayment]


class SpendingCalendarReport(BaseModel):
    valuation_ccy: str
    start_date: date
    end_date: date
    max_daily_spending: float
    days: list[SpendingCalendarDay]


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
