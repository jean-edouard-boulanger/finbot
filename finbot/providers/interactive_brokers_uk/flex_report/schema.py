from datetime import date, datetime
from enum import Enum

from finbot.core.schema import BaseModel, CurrencyCode


class TradeDirection(str, Enum):
    buy = "buy"
    sell = "sell"


class Trade(BaseModel):
    currency: CurrencyCode
    fx_rate_to_base: float
    asset_category: str
    sub_category: str
    symbol: str
    description: str
    contract_identifier: str
    security_id: str
    security_id_type: str
    cusip: str
    isin: str
    listing_exchange: str
    trade_id: str
    trade_time: datetime
    transaction_type: str
    exchange: str
    quantity: float
    trade_price: float
    trade_money: float
    proceeds: float
    ib_commission: float
    ib_commission_ccy: CurrencyCode
    net_cash: float
    net_cash_in_base: float
    close_price: float
    open_close_indicator: str
    fifo_pnl_realized: float
    capital_gains_pnl: float
    buy_sell: TradeDirection
    ib_order_id: str
    transaction_id: str
    order_type: str
    report_date: date


class Trades(BaseModel):
    entries: list[Trade]


class CashTransaction(BaseModel):
    currency: CurrencyCode
    fx_rate_to_base: float
    description: str
    settlement_date: date
    amount: float
    transaction_type: str
    transaction_id: str
    report_date: date


class PositionSide(str, Enum):
    long = "long"
    short = "short"


class MTMPerformanceSummaryUnderlying(BaseModel):
    asset_category: str
    sub_category: str
    symbol: str
    description: str
    security_id: str
    security_id_type: str
    cusip: str
    isin: str
    listing_exchange: str
    close_quantity: float
    close_price: float
    commissions: float

    @property
    def full_security_id(self) -> str:
        return _make_full_security_id(self)


class MTMPerformanceSummaryInBase(BaseModel):
    entries: list[MTMPerformanceSummaryUnderlying]


class OpenPosition(BaseModel):
    currency: CurrencyCode
    asset_category: str
    sub_category: str
    symbol: str
    description: str
    security_id: str
    security_id_type: str
    cusip: str
    isin: str
    listing_exchange: str
    position: float
    mark_price: float
    position_value: float
    position_value_in_base: float
    side: PositionSide
    report_date: date

    @property
    def full_security_id(self) -> str:
        return _make_full_security_id(self)


class OpenPositions(BaseModel):
    entries: list[OpenPosition]


class CashReportCurrency(BaseModel):
    currency: CurrencyCode
    ending_cash: float


class CashReport(BaseModel):
    entries: list[CashReportCurrency]


class SecurityInfo(BaseModel):
    currency: CurrencyCode
    asset_category: str
    sub_category: str
    symbol: str
    description: str
    security_id: str
    security_id_type: str
    listing_exchange: str

    @property
    def full_security_id(self) -> str:
        return _make_full_security_id(self)


class SecuritiesInfo(BaseModel):
    entries: list[SecurityInfo]


class ConversionRate(BaseModel):
    from_currency: CurrencyCode
    to_currency: CurrencyCode
    rate: float
    report_date: date


class ConversionRates(BaseModel):
    entries: list[ConversionRate]


class AccountInformation(BaseModel):
    account_id: str
    alias: str
    currency: CurrencyCode


class FlexStatementEntries(BaseModel):
    account_information: AccountInformation | None = None
    mtm_performance_summary_in_base: MTMPerformanceSummaryInBase | None = None
    securities_info: SecuritiesInfo | None = None
    conversion_rates: ConversionRates | None = None
    open_positions: OpenPositions | None = None
    cash_report: CashReport | None = None
    trades: Trades | None = None


class FlexStatement(BaseModel):
    account_id: str
    from_date: date
    to_date: date
    period: str
    entries: FlexStatementEntries


class FlexReport(BaseModel):
    query_name: str
    statements: list[FlexStatement]
    messages: list[str]


def _make_full_security_id(
    entry: MTMPerformanceSummaryUnderlying | SecurityInfo | OpenPosition,
) -> str:
    return f"{entry.asset_category}:{entry.security_id_type}:{entry.security_id}"
