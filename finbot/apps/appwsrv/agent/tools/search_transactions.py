from datetime import date, datetime, timezone

from pydantic import Field

from finbot.apps.appwsrv.agent import schema as agent_schema
from finbot.apps.appwsrv.agent.tools.base import ToolResult, data_tool
from finbot.apps.appwsrv.reports.transactions import report as transactions_report
from finbot.core.schema import BaseModel
from finbot.model import SessionType


class _Args(BaseModel):
    from_date: date | None = Field(default=None, description="Start of the date range (inclusive).")
    to_date: date | None = Field(default=None, description="End of the date range (inclusive).")
    description: str | None = Field(default=None, description="Substring match on transaction description.")
    merchant_name: list[str] | None = Field(default=None, description="Filter by merchant name(s).")
    spending_category: list[str] | None = Field(default=None, description="Filter by spending category code(s).")
    amount_sign: agent_schema.AmountSign | None = Field(default=None, description="Filter to credits or debits only.")
    amount_min: float | None = Field(default=None, description="Absolute amount lower bound.")
    amount_max: float | None = Field(default=None, description="Absolute amount upper bound.")
    limit: int = Field(default=20, ge=1, le=50, description="Max number of rows to return (capped at 50).")


class _Transaction(BaseModel):
    date: str
    amount: float
    currency: str
    description: str
    merchant: str | None
    category: str | None
    account_name: str
    transaction_type: str


class _Payload(BaseModel):
    valuation_currency: str
    total_count: int
    returned_count: int
    transactions: list[_Transaction]


@data_tool(
    description=(
        "Search transactions with optional filters. Returns at most 50 rows ordered by date desc. "
        "Use for specific transaction lookups; for spending summaries prefer get_spending_breakdown."
    ),
    icon="search",
    label="Querying transactions",
)
def search_transactions(session: SessionType, user_account_id: int, args: _Args) -> ToolResult:
    from_dt = datetime.combine(args.from_date, datetime.min.time(), tzinfo=timezone.utc) if args.from_date else None
    to_dt = datetime.combine(args.to_date, datetime.max.time(), tzinfo=timezone.utc) if args.to_date else None
    report = transactions_report.get_transactions_report(
        session=session,
        user_account_id=user_account_id,
        from_time=from_dt,
        to_time=to_dt,
        description=args.description,
        merchant_name=args.merchant_name,
        spending_category=args.spending_category,
        amount_sign=args.amount_sign.value if args.amount_sign else None,
        amount_min=args.amount_min,
        amount_max=args.amount_max,
        limit=args.limit,
        offset=0,
    )
    txns = [
        _Transaction(
            date=t.transaction_date.date().isoformat(),
            amount=t.amount,
            currency=t.currency,
            description=t.description,
            merchant=t.merchant_name,
            category=t.spending_category_primary,
            account_name=t.linked_account_name,
            transaction_type=t.transaction_type,
        )
        for t in report.transactions
    ]
    payload = _Payload(
        valuation_currency=report.valuation_ccy,
        total_count=report.total_count,
        returned_count=len(txns),
        transactions=txns,
    )
    return ToolResult(payload=payload, summary=f"{report.total_count} transactions")
