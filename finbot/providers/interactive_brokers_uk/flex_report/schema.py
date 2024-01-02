from datetime import date

from finbot.core.schema import BaseModel


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
    report_date: date

    @property
    def full_security_id(self) -> str:
        return _make_full_security_id(self)


class MTMPerformanceSummaryInBase(BaseModel):
    entries: list[MTMPerformanceSummaryUnderlying]


class SecurityInfo(BaseModel):
    currency: str
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
    from_ccy: str
    to_ccy: str
    rate: float


class ConversionRates(BaseModel):
    entries: list[ConversionRate]


class AccountInformation(BaseModel):
    account_id: str
    alias: str
    currency: str


class FlexStatementEntries(BaseModel):
    account_information: AccountInformation | None = None
    mtm_performance_summary_in_base: MTMPerformanceSummaryInBase | None = None
    securities_info: SecuritiesInfo | None = None
    conversion_rates: ConversionRates | None = None


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
    entry: MTMPerformanceSummaryUnderlying | SecurityInfo,
) -> str:
    return f"{entry.asset_category}:{entry.security_id_type}:{entry.security_id}"
