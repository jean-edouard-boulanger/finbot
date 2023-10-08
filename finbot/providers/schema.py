import enum
from typing import Any, NewType, TypeAlias

from pydantic import BaseModel

CurrencyCode = NewType("CurrencyCode", str)
ProviderSpecificPayload: TypeAlias = dict[str, str | int | float | bool]


class AssetClass(str, enum.Enum):
    Equities = "Equities"
    FixedIncome = "FixedIncome"
    Currency = "Currency"
    ForeignCurrency = "ForeignCurrency"
    Crypto = "Crypto"
    RealEstate = "RealEstate"
    Commodities = "Commodities"
    MultiAsset = "MultiAsset"


class AssetType(str, enum.Enum):
    Cash = "Cash"
    Bond = "Bond"
    Stock = "Stock"
    Option = "Option"
    Future = "Future"
    ETF = "ETF"
    ETN = "ETN"
    GenericFund = "GenericFund"
    PreciousMetal = "PreciousMetal"
    Cryptocurrency = "Cryptocurrency"
    UtilityToken = "UtilityToken"
    SecurityToken = "SecurityToken"
    StableCoin = "StableCoin"


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
    asset_class: AssetClass | None
    asset_type: AssetType | None
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
            asset_class=AssetClass.Currency
            if is_domestic
            else AssetClass.ForeignCurrency,
            asset_type=AssetType.Cash,
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
