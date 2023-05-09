from enum import Enum
from typing import Literal, TypeAlias

from pydantic import BaseModel

from finbot.core.schema import CredentialsPayloadType
from finbot.core.web_service import ApplicationErrorData
from finbot.providers import schema as providers_schema


class LineItem(str, Enum):
    Balances = "Balances"
    Assets = "Assets"
    Liabilities = "Liabilities"


class ApplicationError(BaseModel):
    user_message: str
    debug_message: str | None = None
    error_code: str | None = None
    exception_type: str | None = None
    trace: str | None = None


class LineItemError(BaseModel):
    line_item: LineItem
    error: ApplicationErrorData


class BalancesResults(BaseModel):
    line_item: Literal[LineItem.Balances] = LineItem.Balances
    results: list[providers_schema.BalanceEntry]


class AssetsResults(BaseModel):
    line_item: Literal[LineItem.Assets] = LineItem.Assets
    results: list[providers_schema.AssetsEntry]


class LiabilitiesResults(BaseModel):
    line_item: Literal[LineItem.Liabilities] = LineItem.Liabilities
    results: list[providers_schema.LiabilitiesEntry]


LineItemResults: TypeAlias = (
    BalancesResults | AssetsResults | LiabilitiesResults | LineItemError
)


class ValidateCredentialsRequest(BaseModel):
    provider_id: str
    credentials: CredentialsPayloadType


class ValidateCredentialsResponse(BaseModel):
    valid: bool
    error_message: str | None = None


class GetFinancialDataRequest(BaseModel):
    provider_id: str
    credentials: CredentialsPayloadType
    items: list[LineItem]


class GetFinancialDataResponse(BaseModel):
    financial_data: list[LineItemResults]
