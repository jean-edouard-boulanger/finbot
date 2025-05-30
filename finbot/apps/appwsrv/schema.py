from datetime import date, datetime
from typing import Any, Literal, TypeAlias

from finbot.apps.appwsrv.reports.earnings import schema as earnings_schema
from finbot.apps.appwsrv.reports.holdings import schema as holdings_schema
from finbot.core import schema as core_schema
from finbot.core.pydantic_ import Extra, Field, SecretStr
from finbot.core.schema import BaseModel, HexColour
from finbot.providers import schema as providers_schema

JsonSchemaType: TypeAlias = dict[str, Any]
CredentialsSchemaType: TypeAlias = JsonSchemaType
CredentialsPayloadType: TypeAlias = dict[str, Any]


class AppModel(BaseModel):
    __schema_namespace__ = "App"


class UnsetField(AppModel):
    pass


class ErrorMetadata(AppModel):
    user_message: str
    debug_message: str | None
    error_code: str | None
    exception_type: str | None
    trace: str | None

    class Config:
        extra = Extra.ignore


class AuthenticationPayload(AppModel):
    access_token: str
    refresh_token: str


class UserAccountProfile(AppModel):
    email: str
    full_name: str
    mobile_phone_number: str | None


class UserAccountSettings(AppModel):
    valuation_ccy: str
    created_at: datetime
    updated_at: datetime | None


class UserAccount(AppModel):
    id: int
    email: str
    full_name: str
    mobile_phone_number: str | None
    is_demo: bool
    created_at: datetime
    updated_at: datetime | None


class Provider(AppModel):
    id: str
    description: str
    website_url: str
    credentials_schema: CredentialsSchemaType
    created_at: datetime
    updated_at: datetime | None


class LinkedAccountStatusErrorEntry(AppModel):
    scope: str
    error: ErrorMetadata


class LinkedAccountStatus(AppModel):
    status: Literal["stable", "unstable"]
    errors: list[LinkedAccountStatusErrorEntry] | None
    last_snapshot_id: int
    last_snapshot_time: datetime


class LinkedAccount(AppModel):
    id: int
    user_account_id: int
    account_name: str
    account_colour: HexColour
    deleted: bool
    frozen: bool
    provider_id: str
    provider: Provider
    status: LinkedAccountStatus | None
    credentials: CredentialsPayloadType | None
    created_at: datetime
    updated_at: datetime | None


class SystemReport(AppModel):
    finbot_version: str
    finbot_api_version: str
    runtime: str
    is_demo: bool


class LoginRequest(AppModel):
    email: str
    password: str


class LoginResponse(AppModel):
    auth: AuthenticationPayload
    account: UserAccount


class SystemReportResponse(AppModel):
    system_report: SystemReport


class UpdateLinkedAccountMetadataRequest(AppModel):
    account_name: str | None = None
    account_colour: HexColour | None = None
    frozen: bool | None = None


class UpdateLinkedAccountMetadataResponse(AppModel):
    pass


class LinkAccountCommitParams(AppModel):
    do_validate: bool = Field(default=True, alias="validate")
    do_persist: bool = Field(default=True, alias="persist")


class LinkAccountRequest(AppModel):
    provider_id: str
    credentials: CredentialsPayloadType
    account_name: str
    account_colour: HexColour


class LinkAccountResponse(AppModel):
    pass


class UpdateLinkedAccountCredentialsRequest(AppModel):
    credentials: CredentialsPayloadType


class UpdateLinkedAccountCredentialsResponse(AppModel):
    pass


class GetLinkedAccountsResponse(AppModel):
    linked_accounts: list[LinkedAccount]


class GetLinkedAccountResponse(AppModel):
    linked_account: LinkedAccount


class DeleteLinkedAccountResponse(AppModel):
    pass


class CreateOrUpdateProviderRequest(AppModel):
    id: str
    description: str
    website_url: str
    credentials_schema: CredentialsSchemaType


class CreateOrUpdateProviderResponse(AppModel):
    provider: Provider


class GetProvidersResponse(AppModel):
    providers: list[Provider]


class GetProviderResponse(AppModel):
    provider: Provider


class DeleteProviderResponse(AppModel):
    pass


class UserAccountCreationSettings(AppModel):
    valuation_ccy: str


class CreateUserAccountRequest(AppModel):
    email: str
    password: SecretStr
    full_name: str
    settings: UserAccountCreationSettings


class CreateUserAccountResponse(AppModel):
    user_account: UserAccount


class GetUserAccountResponse(AppModel):
    user_account: UserAccount


class UpdateUserAccountPasswordRequest(AppModel):
    old_password: SecretStr
    new_password: SecretStr


class UpdateUserAccountPasswordResponse(AppModel):
    pass


class UpdateUserAccountProfileRequest(AppModel):
    email: str
    full_name: str
    mobile_phone_number: str | None = None


class UpdateUserAccountProfileResponse(AppModel):
    profile: UserAccountProfile


class GetUserAccountSettingsResponse(AppModel):
    settings: UserAccountSettings


class IsUserAccountConfiguredResponse(AppModel):
    configured: bool


class IsEmailAvailableRequestParams(AppModel):
    email: str


class IsEmailAvailableResponse(AppModel):
    available: bool


class TriggerUserAccountValuationResponse(AppModel):
    pass


class UserAccountValuationSparklineEntry(AppModel):
    effective_at: datetime
    value: float | None


class UserAccountValuation(AppModel):
    date: datetime
    currency: str
    value: float
    total_liabilities: float
    change: core_schema.ValuationChange
    sparkline: list[UserAccountValuationSparklineEntry]


class GetUserAccountValuationResponse(AppModel):
    valuation: UserAccountValuation


class GroupValuation(AppModel):
    name: str
    colour: HexColour
    value: float


class ValuationByAssetType(AppModel):
    valuation_ccy: str
    by_asset_type: list[GroupValuation]


class GetUserAccountValuationByAssetTypeResponse(AppModel):
    valuation: ValuationByAssetType


class ValuationByAssetClass(AppModel):
    valuation_ccy: str
    by_asset_class: list[GroupValuation]


class GetUserAccountValuationByAssetClassResponse(AppModel):
    valuation: ValuationByAssetClass


class ValuationByCurrencyExposure(AppModel):
    valuation_ccy: str
    by_currency_exposure: list[GroupValuation]


class GetUserAccountValuationByCurrencyExposureResponse(AppModel):
    valuation: ValuationByCurrencyExposure


class HistoricalValuationParams(AppModel):
    from_time: datetime | None = None
    to_time: datetime | None = None
    frequency: core_schema.ValuationFrequency = core_schema.ValuationFrequency.Daily


class XAxisDescription(AppModel):
    type: str
    categories: list[str | date | datetime]


class SeriesDescription(AppModel):
    name: str
    data: list[int | float | None]
    colour: str


class SeriesData(AppModel):
    x_axis: XAxisDescription
    series: list[SeriesDescription]


class HistoricalValuation(AppModel):
    valuation_ccy: str
    series_data: SeriesData


class GetUserAccountValuationHistoryResponse(AppModel):
    historical_valuation: HistoricalValuation


class GetUserAccountValuationHistoryByAssetTypeResponse(AppModel):
    historical_valuation: HistoricalValuation


class GetUserAccountValuationHistoryByAssetClassResponse(AppModel):
    historical_valuation: HistoricalValuation


class LinkedAccountValuation(AppModel):
    date: datetime
    currency: str
    value: float
    change: core_schema.ValuationChange


class LinkedAccountValuationLinkedAccountDescription(AppModel):
    id: int
    provider_id: str
    description: str
    account_colour: HexColour


class LinkedAccountValuationEntry(AppModel):
    linked_account: LinkedAccountValuationLinkedAccountDescription
    valuation: LinkedAccountValuation


class LinkedAccountsValuation(AppModel):
    valuation_ccy: str
    entries: list[LinkedAccountValuationEntry]


class GetLinkedAccountsValuationResponse(AppModel):
    valuation: LinkedAccountsValuation


class GetLinkedAccountsHistoricalValuation(AppModel):
    historical_valuation: HistoricalValuation


class EmailProviderMetadata(AppModel):
    provider_id: str
    description: str
    settings_schema: dict[str, Any]


class GetEmailDeliveryProvidersResponse(AppModel):
    providers: list[EmailProviderMetadata]


class EmailDeliverySettings(AppModel):
    subject_prefix: str
    sender_name: str
    provider_id: str
    provider_settings: dict[str, Any]


class GetEmailDeliverySettingsResponse(AppModel):
    settings: EmailDeliverySettings | None


class SetEmailDeliverySettingsParams(AppModel):
    do_validate: bool = Field(default=False, alias="validate")


class SetEmailDeliverySettingsResponse(AppModel):
    pass


class RemoveEmailDeliverySettingsResponse(AppModel):
    pass


class GetHoldingsReportResponse(AppModel):
    report: holdings_schema.ValuationTree


class GetEarningsReportResponse(AppModel):
    report: earnings_schema.EarningsReport


class PlaidSettings(AppModel):
    environment: str
    client_id: str
    public_key: str


class GetPlaidSettingsResponse(AppModel):
    settings: PlaidSettings | None


class AssetClassFormattingRule(AppModel):
    asset_class: providers_schema.AssetClass
    pretty_name: str
    dominant_colour: HexColour


class AssetTypeFormattingRule(AppModel):
    asset_type: providers_schema.AssetType
    pretty_name: str
    abbreviated_name: str


class AssetTypeClassFormattingRule(AppModel):
    asset_type: providers_schema.AssetType
    asset_class: providers_schema.AssetClass
    pretty_name: str
    dominant_colour: HexColour


class GetAccountsFormattingRulesResponse(AppModel):
    colour_palette: list[HexColour]
