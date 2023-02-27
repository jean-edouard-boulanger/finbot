from typing import Any, Literal, TypeAlias

from pydantic import BaseModel

from finbot.core.web_service import ApplicationErrorData
from finbot.providers.schema import AssetsEntry, BalanceEntry, LiabilitiesEntry

LineItemType = Literal["balances", "assets", "liabilities"]


class FinancialDataRequest(BaseModel):
    provider: str
    credentials: dict[str, Any]
    items: list[LineItemType]
    account_metadata: str | None = None


class ApplicationError(BaseModel):
    user_message: str
    debug_message: str | None = None
    error_code: str | None = None
    exception_type: str | None = None
    trace: str | None = None


class LineItemError(BaseModel):
    line_item: LineItemType
    error: ApplicationErrorData


class BalancesResults(BaseModel):
    line_item: LineItemType = "balances"
    results: list[BalanceEntry]


class AssetsResults(BaseModel):
    line_item: LineItemType = "assets"
    results: list[AssetsEntry]


class LiabilitiesResults(BaseModel):
    line_item: LineItemType = "liabilities"
    results: list[LiabilitiesEntry]


LineItemResults: TypeAlias = (
    BalancesResults | AssetsResults | LiabilitiesResults | LineItemError
)


class FinancialDataResponse(BaseModel):
    financial_data: list[LineItemResults]


class HealthResponse(BaseModel):
    healthy: bool
