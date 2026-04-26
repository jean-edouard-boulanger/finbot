from enum import Enum
from typing import Literal, Union

from pydantic import Field

from finbot.apps.appwsrv.schema import AppModel

# ---------- Request ----------


class ChatMessage(AppModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(AppModel):
    messages: list[ChatMessage] = Field(min_length=1)


# ---------- Shared enums ----------


class AmountSign(str, Enum):
    credit = "credit"
    debit = "debit"


# ---------- Rich blocks (mirrors webapp/src/components/chat-drawer/types.ts — keep in sync) ----------


class KvRow(AppModel):
    label: str
    value: str
    tone: Literal["up", "down", "neutral"] | None = None


class KvBlock(AppModel):
    kind: Literal["kv"] = "kv"
    title: str
    rows: list[KvRow] = Field(min_length=1, max_length=12)


class TableBlock(AppModel):
    kind: Literal["table"] = "table"
    title: str
    headers: list[str] = Field(min_length=1, max_length=5)
    rows: list[list[str]] = Field(min_length=1, max_length=12)
    footer: str | None = None


class CalloutBlock(AppModel):
    kind: Literal["callout"] = "callout"
    tone: Literal["success", "warning"]
    title: str
    body: str


class ChartSeries(AppModel):
    name: str = Field(description="Series label shown in the legend / tooltip.")
    data: list[float | None] = Field(description="One value per x-axis label, in the same order. Use null for gaps.")


class ChartBlock(AppModel):
    kind: Literal["chart"] = "chart"
    chart_type: Literal["line", "area", "bar"]
    title: str
    x_axis_labels: list[str] = Field(min_length=2, max_length=36)
    series: list[ChartSeries] = Field(min_length=1, max_length=5)
    y_unit: str | None = Field(
        default=None,
        description=(
            "Optional formatting hint for the Y axis and tooltip. Use a 3-letter currency code "
            "(e.g. 'GBP', 'USD') for monetary axes, or '%' for percentage. Omit for plain numbers."
        ),
    )
    footer: str | None = Field(default=None, description="Optional one-line caption below the chart.")


class ClarificationOption(AppModel):
    label: str = Field(description="Short button text shown to the user.")
    send_text: str = Field(
        description="What gets sent back as a user message when this option is clicked.",
    )


class ClarificationBlock(AppModel):
    kind: Literal["clarification"] = "clarification"
    title: str = Field(description="The question to put to the user, e.g. 'Which month did you mean?'")
    options: list[ClarificationOption] = Field(min_length=2, max_length=4)


RichBlock = Union[KvBlock, TableBlock, CalloutBlock, ChartBlock, ClarificationBlock]
