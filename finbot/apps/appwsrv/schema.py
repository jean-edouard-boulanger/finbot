from datetime import date, datetime
from typing import Any, Literal, TypeAlias

from pydantic import Extra, Field, SecretStr

from finbot.apps.appwsrv.reports.earnings import schema as earnings_schema
from finbot.apps.appwsrv.reports.holdings import schema as holdings_schema
from finbot.core import schema as core_schema
from finbot.core.schema import BaseModel, HexColour
from finbot.providers import schema as providers_schema

JsonSchemaType: TypeAlias = dict[str, Any]
CredentialsSchemaType: TypeAlias = JsonSchemaType
CredentialsPayloadType: TypeAlias = dict[str, Any]


class UnsetField(BaseModel):
    pass


class ErrorMetadata(BaseModel):
    user_message: str
    debug_message: str | None
    error_code: str | None
    exception_type: str | None
    trace: str | None

    class Config:
        extra = Extra.ignore


class AuthenticationPayload(BaseModel):
    access_token: str
    refresh_token: str


class UserAccountProfile(BaseModel):
    email: str
    full_name: str
    mobile_phone_number: str | None


class UserAccountSettings(BaseModel):
    valuation_ccy: str
    created_at: datetime
    updated_at: datetime | None


class UserAccount(BaseModel):
    id: int
    email: str
    full_name: str
    mobile_phone_number: str | None
    created_at: datetime
    updated_at: datetime | None


class Provider(BaseModel):
    id: str
    description: str
    website_url: str
    credentials_schema: CredentialsSchemaType
    created_at: datetime
    updated_at: datetime | None


class LinkedAccountStatusErrorEntry(BaseModel):
    scope: str
    error: ErrorMetadata


class LinkedAccountStatus(BaseModel):
    status: Literal["stable", "unstable"]
    errors: list[LinkedAccountStatusErrorEntry] | None
    last_snapshot_id: int
    last_snapshot_time: datetime


class LinkedAccount(BaseModel):
    id: int
    user_account_id: int
    account_name: str
    deleted: bool
    frozen: bool
    provider_id: str
    provider: Provider
    status: LinkedAccountStatus | None
    credentials: CredentialsPayloadType | None
    created_at: datetime
    updated_at: datetime | None


class SystemReport(BaseModel):
    finbot_version: str
    runtime: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    auth: AuthenticationPayload
    account: UserAccount


class SystemReportResponse(BaseModel):
    system_report: SystemReport


class UpdateLinkedAccountMetadataRequest(BaseModel):
    account_name: str | None = None
    frozen: bool | None = None


class UpdateLinkedAccountMetadataResponse(BaseModel):
    pass


class LinkAccountCommitParams(BaseModel):
    do_validate: bool = Field(default=True, alias="validate")
    do_persist: bool = Field(default=True, alias="persist")


class LinkAccountRequest(BaseModel):
    provider_id: str
    credentials: CredentialsPayloadType
    account_name: str


class LinkAccountResponse(BaseModel):
    pass


class UpdateLinkedAccountCredentialsRequest(BaseModel):
    credentials: CredentialsPayloadType


class UpdateLinkedAccountCredentialsResponse(BaseModel):
    pass


class GetLinkedAccountsResponse(BaseModel):
    linked_accounts: list[LinkedAccount]


class GetLinkedAccountResponse(BaseModel):
    linked_account: LinkedAccount


class DeleteLinkedAccountResponse(BaseModel):
    pass


class CreateOrUpdateProviderRequest(BaseModel):
    id: str
    description: str
    website_url: str
    credentials_schema: CredentialsSchemaType


class CreateOrUpdateProviderResponse(BaseModel):
    provider: Provider


class GetProvidersResponse(BaseModel):
    providers: list[Provider]


class GetProviderResponse(BaseModel):
    provider: Provider


class DeleteProviderResponse(BaseModel):
    pass


class UserAccountCreationSettings(BaseModel):
    valuation_ccy: str


class CreateUserAccountRequest(BaseModel):
    email: str
    password: SecretStr
    full_name: str
    settings: UserAccountCreationSettings


class CreateUserAccountResponse(BaseModel):
    user_account: UserAccount


class GetUserAccountResponse(BaseModel):
    user_account: UserAccount


class UpdateUserAccountPasswordRequest(BaseModel):
    old_password: SecretStr
    new_password: SecretStr


class UpdateUserAccountPasswordResponse(BaseModel):
    pass


class UpdateUserAccountProfileRequest(BaseModel):
    email: str
    full_name: str
    mobile_phone_number: str | None = None


class UpdateUserAccountProfileResponse(BaseModel):
    profile: UserAccountProfile


class GetUserAccountSettingsResponse(BaseModel):
    settings: UserAccountSettings


class IsUserAccountConfiguredResponse(BaseModel):
    configured: bool


class IsEmailAvailableRequestParams(BaseModel):
    email: str


class IsEmailAvailableResponse(BaseModel):
    available: bool


class UserAccountValuationSparklineEntry(BaseModel):
    effective_at: datetime
    value: float | None


class UserAccountValuation(BaseModel):
    date: datetime
    currency: str
    value: float
    total_liabilities: float
    change: core_schema.ValuationChange
    sparkline: list[UserAccountValuationSparklineEntry]


class GetUserAccountValuationResponse(BaseModel):
    valuation: UserAccountValuation


class GroupValuation(BaseModel):
    name: str
    colour: HexColour
    value: float


class ValuationByAssetType(BaseModel):
    valuation_ccy: str
    by_asset_type: list[GroupValuation]


class GetUserAccountValuationByAssetTypeResponse(BaseModel):
    valuation: ValuationByAssetType


class ValuationByAssetClass(BaseModel):
    valuation_ccy: str
    by_asset_class: list[GroupValuation]


class GetUserAccountValuationByAssetClassResponse(BaseModel):
    valuation: ValuationByAssetClass


class HistoricalValuationParams(BaseModel):
    from_time: datetime | None = None
    to_time: datetime | None = None
    frequency: core_schema.ValuationFrequency = core_schema.ValuationFrequency.Daily


class XAxisDescription(BaseModel):
    type: str
    categories: list[str | date | datetime]


class SeriesDescription(BaseModel):
    name: str
    data: list[int | float | None]


class SeriesData(BaseModel):
    x_axis: XAxisDescription
    series: list[SeriesDescription]


class HistoricalValuation(BaseModel):
    valuation_ccy: str
    series_data: SeriesData


class GetUserAccountValuationHistoryResponse(BaseModel):
    historical_valuation: HistoricalValuation


class GetUserAccountValuationHistoryByAssetTypeResponse(BaseModel):
    historical_valuation: HistoricalValuation


class LinkedAccountValuation(BaseModel):
    date: datetime
    currency: str
    value: float
    change: core_schema.ValuationChange


class LinkedAccountValuationLinkedAccountDescription(BaseModel):
    id: int
    provider_id: str
    description: str
    account_colour: HexColour


class LinkedAccountValuationEntry(BaseModel):
    linked_account: LinkedAccountValuationLinkedAccountDescription
    valuation: LinkedAccountValuation


class LinkedAccountsValuation(BaseModel):
    valuation_ccy: str
    entries: list[LinkedAccountValuationEntry]


class GetLinkedAccountsValuationResponse(BaseModel):
    valuation: LinkedAccountsValuation


class GetLinkedAccountsHistoricalValuation(BaseModel):
    historical_valuation: HistoricalValuation


class EmailProviderMetadata(BaseModel):
    provider_id: str
    description: str
    settings_schema: dict[str, Any]


class GetEmailDeliveryProvidersResponse(BaseModel):
    providers: list[EmailProviderMetadata]


class EmailDeliverySettings(BaseModel):
    subject_prefix: str
    sender_name: str
    provider_id: str
    provider_settings: dict[str, Any]


class GetEmailDeliverySettingsResponse(BaseModel):
    settings: EmailDeliverySettings | None


class SetEmailDeliverySettingsParams(BaseModel):
    do_validate: bool = Field(default=False, alias="validate")


class SetEmailDeliverySettingsResponse(BaseModel):
    pass


class RemoveEmailDeliverySettingsResponse(BaseModel):
    pass


class GetHoldingsReportResponse(BaseModel):
    report: holdings_schema.ValuationTree


class GetEarningsReportResponse(BaseModel):
    report: earnings_schema.EarningsReport


class PlaidSettings(BaseModel):
    environment: str
    client_id: str
    public_key: str


class GetPlaidSettingsResponse(BaseModel):
    settings: PlaidSettings | None


class AssetClassFormattingRule(BaseModel):
    asset_class: providers_schema.AssetClass
    pretty_name: str
    dominant_colour: HexColour


class AssetTypeFormattingRule(BaseModel):
    asset_type: providers_schema.AssetType
    pretty_name: str
    abbreviated_name: str


class AssetTypeClassFormattingRule(BaseModel):
    asset_type: providers_schema.AssetType
    asset_class: providers_schema.AssetClass
    pretty_name: str
    dominant_colour: HexColour
