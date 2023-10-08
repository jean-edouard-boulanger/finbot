from typing import Literal

from finbot.core import schema as core_schema
from finbot.core.schema import BaseModel


class Valuation(BaseModel):
    currency: str
    value: float
    change: core_schema.ValuationChange


class ValuationWithSparkline(Valuation):
    sparkline: list[float | None]


class SubAccountItemMetadataNode(BaseModel):
    role: Literal["metadata"] = "metadata"
    label: str
    value: int | float | str | bool


class SubAccountItemDescription(BaseModel):
    name: str
    type: str
    sub_type: str
    asset_class: str | None
    asset_type: str | None


class SubAccountItemNode(BaseModel):
    role: Literal["item"] = "item"
    item: SubAccountItemDescription
    valuation: Valuation
    children: list[SubAccountItemMetadataNode]


class SubAccountDescription(BaseModel):
    id: str
    currency: str
    description: str
    type: str


class SubAccountNode(BaseModel):
    role: Literal["sub_account"] = "sub_account"
    sub_account: SubAccountDescription
    valuation: Valuation
    children: list[SubAccountItemNode]


class LinkedAccountDescription(BaseModel):
    id: int
    provider_id: str
    description: str


class LinkedAccountNode(BaseModel):
    role: Literal["linked_account"] = "linked_account"
    linked_account: LinkedAccountDescription
    valuation: ValuationWithSparkline
    children: list[SubAccountNode]


class UserAccountNode(BaseModel):
    role: Literal["user_account"] = "user_account"
    valuation: ValuationWithSparkline
    children: list[LinkedAccountNode]


class ValuationTree(BaseModel):
    valuation_tree: UserAccountNode
