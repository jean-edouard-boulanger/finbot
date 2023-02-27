from typing import Any

from pydantic import BaseModel


class Account(BaseModel):
    id: str
    name: str
    iso_currency: str
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


class LiabilitiesEntry(BaseModel):
    account: Account
    liabilities: list[Liability]


class Liabilities(BaseModel):
    accounts: list[LiabilitiesEntry]
