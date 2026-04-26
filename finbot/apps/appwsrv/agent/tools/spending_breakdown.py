from datetime import date, datetime, timezone

from pydantic import Field

from finbot.apps.appwsrv.agent.tools.base import ToolResult, data_tool
from finbot.apps.appwsrv.reports.transactions import report as transactions_report
from finbot.core.schema import BaseModel
from finbot.model import SessionType


class _Args(BaseModel):
    from_date: date = Field(description="Start of the date range (inclusive).")
    to_date: date = Field(description="End of the date range (inclusive).")


class _Entry(BaseModel):
    category: str
    total: float
    transaction_count: int


class _Payload(BaseModel):
    valuation_currency: str
    from_date: str
    to_date: str
    entries: list[_Entry]


@data_tool(
    description=(
        "Get spending grouped by category over a date range. "
        "Use for 'what did I spend on X this month' style questions."
    ),
    icon="credit-card",
    label="Categorising spending",
)
def get_spending_breakdown(session: SessionType, user_account_id: int, args: _Args) -> ToolResult:
    from_dt = datetime.combine(args.from_date, datetime.min.time(), tzinfo=timezone.utc)
    to_dt = datetime.combine(args.to_date, datetime.max.time(), tzinfo=timezone.utc)
    report = transactions_report.get_spending_breakdown(session, user_account_id, from_dt, to_dt)
    payload = _Payload(
        valuation_currency=report.valuation_ccy,
        from_date=args.from_date.isoformat(),
        to_date=args.to_date.isoformat(),
        entries=[
            _Entry(category=e.category, total=e.total, transaction_count=e.transaction_count) for e in report.entries
        ],
    )
    return ToolResult(payload=payload, summary=f"{len(report.entries)} categories")
