from typing import Any

from pydantic import Field

from finbot.apps.appwsrv.agent.tools.base import ToolResult, data_tool
from finbot.apps.appwsrv.reports.transactions import report as transactions_report
from finbot.core.schema import BaseModel
from finbot.model import SessionType


class _Args(BaseModel):
    comparison_month: str | None = Field(
        default=None,
        description="YYYY-MM format. Defaults to the previous calendar month.",
        pattern=r"^\d{4}-\d{2}$",
    )


class _MonthlySavings(BaseModel):
    month: str
    income: float
    expenses: float
    savings: float
    savings_rate: float | None
    projected_savings: float | None = None
    projected_savings_rate: float | None = None


class _Payload(BaseModel):
    valuation_currency: str
    current_month: _MonthlySavings
    comparison_month: _MonthlySavings


@data_tool(
    description="Get the savings rate for the current month and a comparison month (defaults to previous month).",
    icon="piggy",
    label="Computing savings rate",
)
def get_savings_rate(session: SessionType, user_account_id: int, args: _Args) -> ToolResult:
    report = transactions_report.get_savings_rate_report(session, user_account_id, args.comparison_month)

    def to_monthly(entry: Any) -> _MonthlySavings:
        return _MonthlySavings(
            month=entry.month,
            income=entry.income,
            expenses=entry.expenses,
            savings=entry.savings,
            savings_rate=entry.savings_rate,
            projected_savings=entry.projected_savings,
            projected_savings_rate=entry.projected_savings_rate,
        )

    payload = _Payload(
        valuation_currency=report.valuation_ccy,
        current_month=to_monthly(report.current_month),
        comparison_month=to_monthly(report.comparison_month),
    )
    rate = report.current_month.savings_rate
    summary = f"{rate * 100:.0f}% current month" if rate is not None else "current month"
    return ToolResult(payload=payload, summary=summary)
