from enum import Enum
from typing import Literal, TypeAlias

from pydantic import AwareDatetime

from finbot.core.schema import ApplicationErrorData, BaseModel, CurrencyCode, EncryptedCredentialsPayloadType
from finbot.providers import schema as providers_schema


class LineItem(str, Enum):
    Accounts = "Accounts"
    Assets = "Assets"
    Liabilities = "Liabilities"
    Transactions = "Transactions"


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


class TransactionsResults(BaseModel):
    line_item: Literal[LineItem.Transactions] = LineItem.Transactions
    results: list[providers_schema.Transaction]


LineItemResults: TypeAlias = AccountsResults | AssetsResults | LiabilitiesResults | TransactionsResults | LineItemError


class ValidateCredentialsRequest(BaseModel):
    provider_id: str
    encrypted_credentials: EncryptedCredentialsPayloadType
    user_account_currency: CurrencyCode


class ValidateCredentialsResponse(BaseModel):
    valid: bool
    error_message: str | None = None


class GetFinancialDataRequest(BaseModel):
    provider_id: str
    encrypted_credentials: EncryptedCredentialsPayloadType
    items: list[LineItem]
    user_account_currency: CurrencyCode
    transactions_from_date: AwareDatetime | None = None


class GetFinancialDataResponse(BaseModel):
    financial_data: list[LineItemResults]
    error: ApplicationErrorData | None = None
