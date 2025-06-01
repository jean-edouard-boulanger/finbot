import enum
from typing import Literal

from finbot.core import schema as core_schema
from finbot.core.schema import BaseModel
from finbot.providers.schema import AssetClass, AssetType


class Valuation(BaseModel):
    currency: str
    value: float
    change: core_schema.ValuationChange


class ValuationWithSparkline(Valuation):
    sparkline: list[float | None]


class NodeRole(str, enum.Enum):
    metadata = "metadata"
    item = "item"
    sub_account = "sub_account"
    linked_account = "linked_account"
    user_account = "user_account"


class SubAccountItemMetadataNode(BaseModel):
    role: Literal[NodeRole.metadata] = NodeRole.metadata
    label: str
    value: int | float | str | bool


class SubAccountItemNodeIcon(BaseModel):
    background_colour: core_schema.HexColour
    label: str
    tooltip: str


class SubAccountItemDescription(BaseModel):
    name: str
    type: str
    sub_type: str
    asset_class: str | None
    asset_type: str | None
    icon: SubAccountItemNodeIcon | None


class SubAccountItemNode(BaseModel):
    role: Literal[NodeRole.item] = NodeRole.item
    item: SubAccountItemDescription
    valuation: Valuation
    children: list[SubAccountItemMetadataNode]


class SubAccountDescription(BaseModel):
    id: str
    currency: str
    description: str
    type: str


class SubAccountNode(BaseModel):
    role: Literal[NodeRole.sub_account] = NodeRole.sub_account
    sub_account: SubAccountDescription
    valuation: Valuation
    children: list[SubAccountItemNode]


class LinkedAccountDescription(BaseModel):
    id: int
    provider_id: str
    description: str


class LinkedAccountNode(BaseModel):
    role: Literal[NodeRole.linked_account] = NodeRole.linked_account
    linked_account: LinkedAccountDescription
    valuation: ValuationWithSparkline
    children: list[SubAccountNode]


class UserAccountNode(BaseModel):
    role: Literal[NodeRole.user_account] = NodeRole.user_account
    valuation: ValuationWithSparkline
    children: list[LinkedAccountNode]


class AssetTypeFormattingRule(BaseModel):
    asset_type: AssetType
    abbreviated_name: str


class AssetClassFormattingRule(BaseModel):
    asset_class: AssetClass
    background_colour_hex: str


class FormattingRules(BaseModel):
    asset_types: list[AssetTypeFormattingRule]
    asset_classes: list[AssetClassFormattingRule]


class ValuationTree(BaseModel):
    valuation_tree: UserAccountNode
