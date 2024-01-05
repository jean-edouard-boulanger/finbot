import enum
from typing import TypeAlias

from finbot.core.pydantic_ import Field
from finbot.core.schema import BaseModel, CurrencyCode

ProviderSpecificPayloadType: TypeAlias = dict[str, str | int | float | bool]
SchemaNamespace = "Providers"


class AssetClass(str, enum.Enum):
    equities = "equities"
    fixed_income = "fixed_income"
    private_debt = "private_debt"
    currency = "currency"
    foreign_currency = "foreign_currency"
    crypto = "crypto"
    real_estate = "real_estate"
    commodities = "commodities"
    multi_asset = "multi_asset"


class AssetType(str, enum.Enum):
    cash = "cash"
    bond = "bond"
    stock = "stock"
    option = "option"
    future = "future"
    ETF = "ETF"
    ETN = "ETN"
    ETC = "ETC"
    generic_fund = "generic_fund"
    loan = "loan"
    precious_metal = "precious_metal"
    crypto_currency = "crypto_currency"
    utility_token = "utility_token"
    security_token = "security_token"
    stable_coin = "stable_coin"


class Account(BaseModel):
    id: str = Field(description="Account identifier (unique across all accounts in this linked account)")
    name: str = Field(description="Account name/description")
    iso_currency: CurrencyCode = Field(description="Account currency")
    type: str = Field(description="Account type (depository, investment, etc.)")  # TODO: constrain this with an enum


class BalanceEntry(BaseModel):
    account: Account
    balance: float = Field(description="Account balance (in the account currency)")


class Balances(BaseModel):
    accounts: list[BalanceEntry]


class Asset(BaseModel):
    name: str = Field(description="Asset name/description")
    type: str  # deprecated
    asset_class: AssetClass = Field(description="Asset class")
    asset_type: AssetType = Field(description="Asset type")
    value_in_account_ccy: float = Field(description="Asset value in the holding account currency")
    units: float | None = Field(default=None, description="Number of asset units held in the account")
    currency: CurrencyCode | None = Field(default=None, description="Asset currency")
    provider_specific: ProviderSpecificPayloadType | None = Field(
        default=None,
        description="Arbitrary data (key/value pair) specific to the provider/asset",
    )

    @classmethod
    def cash(
        cls,
        currency: CurrencyCode,
        is_domestic: bool,
        amount: float,
        provider_specific: ProviderSpecificPayloadType | None = None,
    ) -> "Asset":
        _validate_currency_code(currency)
        return Asset(
            name=currency.upper(),
            type="currency",  # deprecated
            asset_class=(AssetClass.currency if is_domestic else AssetClass.foreign_currency),
            asset_type=AssetType.cash,
            value_in_account_ccy=amount,
            units=None,
            currency=CurrencyCode(currency.upper()),
            provider_specific=provider_specific,
        )


class AssetsEntry(BaseModel):
    account: Account = Field(description="Account holding the assets")
    assets: list[Asset] = Field(description="Assets held in the account")


class Assets(BaseModel):
    accounts: list[AssetsEntry]


class Liability(BaseModel):
    name: str = Field(description="Liability name/description")
    type: str = Field(description="Liability type (credit, loan, etc.)")  # TODO: constrain this with an enum
    value_in_account_ccy: float = Field(description="Liability amount in the holding account currency")
    provider_specific: ProviderSpecificPayloadType | None = Field(
        default=None,
        description="Arbitrary data (key/value pair) specific to the provider/asset",
    )


class LiabilitiesEntry(BaseModel):
    account: Account = Field(description="Account holding the liabilities")
    liabilities: list[Liability] = Field(description="Liabilities held in the account")


class Liabilities(BaseModel):
    accounts: list[LiabilitiesEntry]


ItemType: TypeAlias = Asset | Liability


def _validate_currency_code(currency: CurrencyCode) -> None:
    if len(currency) != 3 or not all(c.isalnum() for c in currency):
        raise ValueError(f"invalid currency code: {currency}")
