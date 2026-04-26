from finbot.apps.appwsrv.agent.tools.base import NoArgs, ToolResult, data_tool
from finbot.apps.appwsrv.reports.transactions import report as transactions_report
from finbot.core.schema import BaseModel
from finbot.model import SessionType


class _Subscription(BaseModel):
    merchant_name: str
    description: str | None
    currency: str
    avg_amount: float
    avg_interval_days: float
    yearly_cost: float
    total_spent_this_year: float


class _Payload(BaseModel):
    valuation_currency: str
    estimated_yearly_total: float
    total_spent_this_year: float
    subscriptions: list[_Subscription]


@data_tool(
    description="Get the user's active recurring subscriptions with average amount, cadence and yearly cost.",
    icon="refresh",
    label="Scanning recurring transactions",
)
def get_subscriptions(session: SessionType, user_account_id: int, args: NoArgs) -> ToolResult:
    report = transactions_report.get_subscriptions_report(session, user_account_id)
    subs = [
        _Subscription(
            merchant_name=s.merchant_name,
            description=s.description,
            currency=s.currency,
            avg_amount=s.avg_amount,
            avg_interval_days=s.avg_interval_days,
            yearly_cost=s.yearly_cost,
            total_spent_this_year=s.total_spent_this_year,
        )
        for s in report.subscriptions
    ]
    payload = _Payload(
        valuation_currency=report.valuation_ccy,
        estimated_yearly_total=report.estimated_yearly_total,
        total_spent_this_year=report.total_spent_this_year,
        subscriptions=subs,
    )
    return ToolResult(payload=payload, summary=f"{len(subs)} active subscriptions")
