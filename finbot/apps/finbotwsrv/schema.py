from enum import Enum
from typing import Literal, TypeAlias

from finbot.core.schema import ApplicationErrorData, BaseModel, CredentialsPayloadType, CurrencyCode
from finbot.providers import schema as providers_schema


class LineItem(str, Enum):
    Accounts = "Accounts"
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


class AccountsResults(BaseModel):
    line_item: Literal[LineItem.Accounts] = LineItem.Accounts
    results: list[providers_schema.Account]


class AssetsResults(BaseModel):
    line_item: Literal[LineItem.Assets] = LineItem.Assets
    results: list[providers_schema.AssetsEntry]


class LiabilitiesResults(BaseModel):
    line_item: Literal[LineItem.Liabilities] = LineItem.Liabilities
    results: list[providers_schema.LiabilitiesEntry]


LineItemResults: TypeAlias = AccountsResults | AssetsResults | LiabilitiesResults | LineItemError


class ValidateCredentialsRequest(BaseModel):
    provider_id: str
    credentials: CredentialsPayloadType
    user_account_currency: CurrencyCode


class ValidateCredentialsResponse(BaseModel):
    valid: bool
    error_message: str | None = None


class GetFinancialDataRequest(BaseModel):
    provider_id: str
    credentials: CredentialsPayloadType
    items: list[LineItem]
    user_account_currency: CurrencyCode


class GetFinancialDataResponse(BaseModel):
    financial_data: list[LineItemResults]
    error: ApplicationErrorData | None = None
