from finbot.apps.appwsrv.agent.tools.base import NoArgs, ToolResult, data_tool
from finbot.core.schema import BaseModel
from finbot.model import SessionType, repository


class _Payload(BaseModel):
    currency: str
    total_value: float
    total_liabilities: float
    as_of: str
    change_1day: float | None
    change_1week: float | None
    change_1month: float | None
    change_1year: float | None


@data_tool(
    description=(
        "Get the user's current total net worth in their valuation currency, "
        "plus changes over the last 1 day, 1 week, 1 month and 1 year."
    ),
    icon="wallet",
    label="Aggregating account valuations",
)
def get_net_worth(session: SessionType, user_account_id: int, args: NoArgs) -> ToolResult:
    last = repository.get_last_history_entry(session, user_account_id)
    uavh = last.user_account_valuation_history_entry
    change = uavh.valuation_change
    payload = _Payload(
        currency=last.valuation_ccy,
        total_value=float(uavh.valuation),
        total_liabilities=float(uavh.total_liabilities),
        as_of=last.effective_at.isoformat(),
        change_1day=float(change.change_1day) if change.change_1day is not None else None,
        change_1week=float(change.change_1week) if change.change_1week is not None else None,
        change_1month=float(change.change_1month) if change.change_1month is not None else None,
        change_1year=float(change.change_1year) if change.change_1year is not None else None,
    )
    return ToolResult(payload=payload, summary=f"as of {last.effective_at.date().isoformat()}")
