import enum
from typing import Any, NewType, TypeAlias

from finbot.core.schema import BaseModel

CurrencyCode = NewType("CurrencyCode", str)
ProviderSpecificPayload: TypeAlias = dict[str, str | int | float | bool]
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
    id: str
    name: str
    iso_currency: CurrencyCode
    type: str


class BalanceEntry(BaseModel):
    account: Account
    balance: float


class Balances(BaseModel):
    accounts: list[BalanceEntry]


class Asset(BaseModel):
    name: str
    type: str  # deprecated
    asset_class: AssetClass
    asset_type: AssetType
    value: float
    units: float | None = None
    provider_specific: dict[str, Any] | None = None

    @classmethod
    def cash(
        cls,
        currency: CurrencyCode,
        is_domestic: bool,
        amount: float,
        provider_specific: dict[str, Any] | None = None,
    ) -> "Asset":
        _validate_currency_code(currency)
        return Asset(
            name=currency.upper(),
            type="currency",  # deprecated
            asset_class=(
                AssetClass.currency if is_domestic else AssetClass.foreign_currency
            ),
            asset_type=AssetType.cash,
            value=amount,
            units=None,
            provider_specific=provider_specific,
        )


class AssetsEntry(BaseModel):
    account: Account
    assets: list[Asset]


class Assets(BaseModel):
    accounts: list[AssetsEntry]


class Liability(BaseModel):
    name: str
    type: str
    value: float
    provider_specific: ProviderSpecificPayload | None = None


class LiabilitiesEntry(BaseModel):
    account: Account
    liabilities: list[Liability]


class Liabilities(BaseModel):
    accounts: list[LiabilitiesEntry]


ItemType: TypeAlias = Asset | Liability


def _validate_currency_code(currency: CurrencyCode) -> None:
    if len(currency) != 3 or not all(c.isalnum() for c in currency):
        raise ValueError(f"invalid currency code: {currency}")
