from typing import Literal

from finbot import model
from finbot.core.schema import BaseModel


class ValuationChange(BaseModel):
    change_1hour: float | None
    change_1day: float | None
    change_1week: float | None
    change_1month: float | None
    change_6months: float | None
    change_1year: float | None
    change_2years: float | None

    @staticmethod
    def from_model(change: model.ValuationChangeEntry):
        return ValuationChange(
            change_1hour=change.change_1hour,
            change_1day=change.change_1day,
            change_1week=change.change_1week,
            change_1month=change.change_1month,
            change_6months=change.change_6months,
            change_1year=change.change_1year,
            change_2years=change.change_2years,
        )


class Valuation(BaseModel):
    currency: str
    value: float
    change: ValuationChange


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
