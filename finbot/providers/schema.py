from typing import Any, TypeAlias

from pydantic import BaseModel

CurrencyCode: TypeAlias = str
ProviderSpecificPayload: TypeAlias = dict[str, str | int | float | bool]


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
    type: str
    value: float
    units: float | None = None
    provider_specific: dict[str, Any] | None = None


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
