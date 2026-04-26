from datetime import date, datetime, timezone

from pydantic import Field

from finbot.apps.appwsrv.agent.tools.base import ToolResult, data_tool
from finbot.core.schema import BaseModel, ValuationFrequency
from finbot.model import SessionType, repository


class _Args(BaseModel):
    from_date: date | None = Field(
        default=None,
        description="Start of the date range (inclusive). Default: 1 year ago.",
    )
    to_date: date | None = Field(default=None, description="End of the date range (inclusive). Default: today.")
    frequency: ValuationFrequency = Field(
        default=ValuationFrequency.Monthly,
        description="Aggregation grain. Daily for ≤2 months, Monthly for up to 2 years, Quarterly/Yearly for longer.",
    )


class _Point(BaseModel):
    period: str
    value: float


class _Payload(BaseModel):
    valuation_currency: str
    frequency: str
    points: list[_Point]


@data_tool(
    description=(
        "Get the user's net-worth time series for charting. Returns one (period, value) point per "
        "frequency bucket within the date range. Use BEFORE present_chart for trend questions like "
        "'how has my net worth changed this year'."
    ),
    icon="trending",
    label="Loading valuation history",
)
def get_valuation_history(session: SessionType, user_account_id: int, args: _Args) -> ToolResult:
    settings = repository.get_user_account_settings(session, user_account_id)
    from_dt = datetime.combine(args.from_date, datetime.min.time(), tzinfo=timezone.utc) if args.from_date else None
    to_dt = datetime.combine(args.to_date, datetime.max.time(), tzinfo=timezone.utc) if args.to_date else None
    history = repository.get_user_account_historical_valuation(
        session=session,
        user_account_id=user_account_id,
        from_time=from_dt,
        to_time=to_dt,
        frequency=args.frequency,
    )
    points = [
        _Point(
            period=(
                entry.valuation_period.isoformat()
                if isinstance(entry.valuation_period, date)
                else entry.valuation_period
            ),
            value=entry.last_value,
        )
        for entry in history
    ]
    payload = _Payload(
        valuation_currency=settings.valuation_ccy,
        frequency=args.frequency.value,
        points=points,
    )
    return ToolResult(payload=payload, summary=f"{len(points)} {args.frequency.value.lower()} points")
