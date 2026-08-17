from datetime import date, datetime
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import ConfigDict, Field, SecretStr, model_validator

from finbot.apps.appwsrv.reports.earnings import schema as earnings_schema
from finbot.apps.appwsrv.reports.holdings import schema as holdings_schema
from finbot.apps.appwsrv.reports.transactions import schema as transactions_schema
from finbot.core import schema as core_schema
from finbot.core.schema import BaseModel, HexColour
from finbot.core.securities_market import SecurityKind
from finbot.providers import schema as providers_schema

JsonSchemaType: TypeAlias = dict[str, Any]
CredentialsSchemaType: TypeAlias = JsonSchemaType
CredentialsPayloadType: TypeAlias = dict[str, Any]


class AppModel(BaseModel):
    pass


class UnsetField(AppModel):
    pass


class ErrorMetadata(AppModel):
    user_message: str
    debug_message: str | None
    error_code: str | None
    exception_type: str | None
    trace: str | None

    model_config = ConfigDict(extra="ignore")


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
    errors: list[LinkedAccountStatusErrorEntry]
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
    portfolio_id: int | None
    """Set when this account is a Finbot managed portfolio, pointing at the portfolio itself."""
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
    do_validate: bool = True
    do_persist: bool = True


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
    linked_account_id: int | None = None


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
    frozen: bool


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


class GetTransactionsReportResponse(AppModel):
    report: transactions_schema.TransactionsReport


class GetCashFlowSummaryResponse(AppModel):
    report: transactions_schema.CashFlowSummary


class GetCashFlowTimeSeriesResponse(AppModel):
    report: transactions_schema.CashFlowTimeSeries


class GetSpendingBreakdownResponse(AppModel):
    report: transactions_schema.SpendingBreakdown


class GetSavingsRateReportResponse(AppModel):
    report: transactions_schema.SavingsRateReport


class GetTransactionResponse(AppModel):
    transaction: transactions_schema.TransactionEntry


class GetTransactionDetailResponse(AppModel):
    transaction: transactions_schema.TransactionDetail


class GetTransactionFilterOptionsResponse(AppModel):
    filter_options: transactions_schema.TransactionFilterOptions


class GetSubscriptionsReportResponse(AppModel):
    report: transactions_schema.SubscriptionsReport


class GetSpendingCalendarResponse(AppModel):
    report: transactions_schema.SpendingCalendarReport


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


class GetAssetsFormattingRulesResponse(AppModel):
    asset_classes: list[AssetClassFormattingRule]
    asset_types: list[AssetTypeFormattingRule]


# `core_schema.CurrencyCode` cannot be used in API schemas: the `examples` it injects is not valid
# under OpenAPI 3.0.3, which the typescript client generator targets.
CurrencyCodeStr = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
PortfolioItemType: TypeAlias = Literal["asset", "liability"]
PortfolioPriceSource: TypeAlias = Literal["manual", "proxy"]
PortfolioCustomColumnType: TypeAlias = Literal["text", "number", "date"]
# Values are kept as plain strings: custom columns are display-only metadata.
PortfolioCustomValuesType: TypeAlias = dict[str, str]


class PortfolioCustomColumn(AppModel):
    # Only constrained in length: keys are also derived from spreadsheet headers when converting an
    # existing account, and those legitimately contain punctuation ("Performance (%)"). A character
    # whitelist here would make an imported portfolio impossible to read back.
    key: str = Field(min_length=1, max_length=64)
    label: str = Field(max_length=64)
    type: PortfolioCustomColumnType = "text"


class PortfolioEntry(AppModel):
    id: int
    item_type: PortfolioItemType
    name: str
    asset_class: providers_schema.AssetClass | None
    asset_type: providers_schema.AssetType | None
    liability_type: str | None
    currency: CurrencyCodeStr
    units: float
    price_source: PortfolioPriceSource
    unit_price: float | None
    """Effective unit price: the manual price, or the last price resolved from the proxy security."""
    manual_unit_price: float | None
    manual_price_updated_at: datetime | None
    proxy_symbol: str | None
    proxy_name: str | None
    """Display name of the proxy security, as it was when the symbol was last resolved."""
    last_resolved_unit_price: float | None
    last_resolved_price_at: datetime | None
    isin_code: str | None
    custom_values: PortfolioCustomValuesType
    value: float | None
    """`units * unit_price`, expressed in the entry currency."""
    estimated_value: float | None
    """Same amount converted to the user's valuation currency. An estimate, see `Portfolio`."""
    display_order: int


class PortfolioSection(AppModel):
    id: int
    section_id: str
    name: str
    currency: CurrencyCodeStr
    account_type: providers_schema.AccountType
    account_sub_type: str | None
    custom_columns: list[PortfolioCustomColumn]
    display_order: int
    estimated_value: float | None
    """Sum of this section's holdings, in the currency this section reports in. An estimate."""
    entries: list[PortfolioEntry]


class PortfolioSummary(AppModel):
    id: int
    linked_account_id: int
    name: str
    colour: HexColour
    frozen: bool
    sections_count: int
    entries_count: int
    estimated_value: float | None
    valuation_ccy: CurrencyCodeStr
    created_at: datetime
    updated_at: datetime | None


class Portfolio(AppModel):
    id: int
    linked_account_id: int
    name: str
    colour: HexColour
    frozen: bool
    estimated_value: float | None
    """Worth of the portfolio in the user's valuation currency.

    An estimate: it uses the prices already on record, including the last price read for tracked
    holdings, so it is available immediately as figures are edited. The confirmed valuation comes
    from the next snapshot.
    """
    valuation_ccy: CurrencyCodeStr
    sections: list[PortfolioSection]
    created_at: datetime
    updated_at: datetime | None


class PortfolioEntryPayload(AppModel):
    """Full description of a portfolio entry: used to both create and replace entries."""

    item_type: PortfolioItemType
    name: str
    asset_class: providers_schema.AssetClass | None = None
    asset_type: providers_schema.AssetType | None = None
    liability_type: str | None = None
    currency: CurrencyCodeStr | None = None
    """Not needed for proxy priced entries: it is derived from the proxy security quote."""
    units: float = 1.0
    price_source: PortfolioPriceSource = "manual"
    manual_unit_price: float | None = None
    proxy_symbol: str | None = None
    isin_code: str | None = None
    custom_values: PortfolioCustomValuesType = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_entry(self) -> "PortfolioEntryPayload":
        if self.item_type == "liability":
            if self.price_source != "manual":
                raise ValueError("Liability entries can only be manually priced")
            if self.asset_class is not None or self.asset_type is not None:
                raise ValueError("Liability entries cannot have an asset class or asset type")
            if not self.liability_type:
                raise ValueError("Liability entries must have a liability type")
        else:
            if self.asset_class is None or self.asset_type is None:
                raise ValueError("Asset entries must have both an asset class and an asset type")
            if self.liability_type is not None:
                raise ValueError("Asset entries cannot have a liability type")
        if self.price_source == "manual":
            if self.manual_unit_price is None:
                raise ValueError("Manually priced entries must have a unit price")
            if self.currency is None:
                raise ValueError("Manually priced entries must have a currency")
        else:
            if not self.proxy_symbol:
                raise ValueError("Proxy priced entries must have a proxy symbol")
        return self


class PortfolioSectionPayload(AppModel):
    """Full description of a portfolio section: used to both create and replace sections."""

    name: str
    currency: CurrencyCodeStr
    account_type: providers_schema.AccountType
    account_sub_type: str | None = None
    custom_columns: list[PortfolioCustomColumn] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_sub_type(self) -> "PortfolioSectionPayload":
        valid_sub_types = providers_schema.VALID_ACCOUNT_SUB_TYPES[self.account_type]
        if self.account_sub_type not in valid_sub_types:
            raise ValueError(
                f"'{self.account_sub_type}' is not a valid sub type for a '{self.account_type.value}' account"
            )
        return self


class AccountSubTypes(AppModel):
    account_type: providers_schema.AccountType
    sub_types: list[str]


class GetAccountSubTypesResponse(AppModel):
    account_sub_types: list[AccountSubTypes]


class CreatePortfolioRequest(AppModel):
    name: str
    colour: HexColour


class CreatePortfolioResponse(AppModel):
    portfolio: Portfolio


class ConversionPreviewHolding(AppModel):
    name: str
    value: float
    currency: CurrencyCodeStr
    is_liability: bool


class ConversionPreviewSection(AppModel):
    name: str
    currency: CurrencyCodeStr
    holdings: list[ConversionPreviewHolding]
    detail_columns: list[str]
    """Extra per holding details that would be carried across, by name."""


class GetConversionPreviewResponse(AppModel):
    account_name: str
    valued_at: datetime | None
    sections: list[ConversionPreviewSection]
    holdings_count: int


class ConvertLinkedAccountRequest(AppModel):
    linked_account_id: int


class ConvertLinkedAccountResponse(AppModel):
    portfolio: Portfolio


class GetPortfoliosResponse(AppModel):
    portfolios: list[PortfolioSummary]


class GetPortfolioResponse(AppModel):
    portfolio: Portfolio


class UpdatePortfolioRequest(AppModel):
    name: str | None = None
    colour: HexColour | None = None


class UpdatePortfolioResponse(AppModel):
    portfolio: Portfolio


class DeletePortfolioResponse(AppModel):
    pass


class CreatePortfolioSectionResponse(AppModel):
    portfolio: Portfolio


class UpdatePortfolioSectionResponse(AppModel):
    portfolio: Portfolio


class DeletePortfolioSectionResponse(AppModel):
    portfolio: Portfolio


class CreatePortfolioEntryResponse(AppModel):
    portfolio: Portfolio


class UpdatePortfolioEntryResponse(AppModel):
    portfolio: Portfolio


class DeletePortfolioEntryResponse(AppModel):
    portfolio: Portfolio


class RefreshPortfolioResponse(AppModel):
    pass


class SecurityQuote(AppModel):
    symbol: str
    name: str | None
    currency: CurrencyCodeStr
    price: float
    as_of: datetime


class ResolveSecurityResponse(AppModel):
    quote: SecurityQuote


class SecuritySearchResult(AppModel):
    symbol: str
    name: str | None
    kind: SecurityKind | None
    exchange: str | None


class SearchSecuritiesResponse(AppModel):
    results: list[SecuritySearchResult]
    #: `False` when Yahoo Finance could not be reached, so that no results can be reported as
    #: "suggestions are unavailable" rather than as "nothing matches".
    provider_available: bool
