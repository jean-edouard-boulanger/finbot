import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv.reports.earnings.report import (
    generate as generate_earnings_report,
)
from finbot.apps.appwsrv.reports.holdings.report import (
    generate as generate_holdings_report,
)
from finbot.apps.appwsrv.reports.transactions.report import (
    get_cash_flow_summary as generate_cash_flow_summary,
)
from finbot.apps.appwsrv.reports.transactions.report import (
    get_cash_flow_time_series as generate_cash_flow_time_series,
)
from finbot.apps.appwsrv.reports.transactions.report import (
    get_spending_breakdown as generate_spending_breakdown,
)
from finbot.apps.appwsrv.reports.transactions.report import (
    get_transactions_report as generate_transactions_report,
)
from finbot.apps.http_base import CurrentUserIdDep
from finbot.core.errors import MissingUserData
from finbot.core.utils import now_utc
from finbot.model import db, repository

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/reports",
    tags=["User accounts (reports)"],
)


@router.get("/holdings/", operation_id="get_user_account_holdings_report")
def get_holdings_report(
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.GetHoldingsReportResponse:
    """Get holdings report"""
    history_entry = repository.get_last_history_entry(db.session, current_user_id)
    if not history_entry:
        raise MissingUserData("No valuation available for selected time range")
    return appwsrv_schema.GetHoldingsReportResponse(
        report=generate_holdings_report(session=db.session, history_entry=history_entry)
    )


@router.get("/earnings/", operation_id="get_user_account_earnings_report")
def get_earnings_report(
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.GetEarningsReportResponse:
    """Get earnings report"""
    to_time = now_utc()
    return appwsrv_schema.GetEarningsReportResponse(
        report=generate_earnings_report(
            session=db.session,
            user_account_id=current_user_id,
            from_time=to_time - timedelta(days=365),
            to_time=to_time,
        )
    )


@router.get("/transactions/", operation_id="get_user_account_transactions_report")
def get_transactions_report(
    current_user_id: CurrentUserIdDep,
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
    linked_account_id: int | None = Query(default=None),
    transaction_category: list[str] | None = Query(default=None),
    spending_category: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
) -> appwsrv_schema.GetTransactionsReportResponse:
    """Get paginated transactions report"""
    return appwsrv_schema.GetTransactionsReportResponse(
        report=generate_transactions_report(
            session=db.session,
            user_account_id=current_user_id,
            from_time=from_time,
            to_time=to_time,
            linked_account_id=linked_account_id,
            transaction_category=transaction_category,
            spending_category=spending_category,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/cash-flow/summary/", operation_id="get_user_account_cash_flow_summary")
def get_cash_flow_summary(
    current_user_id: CurrentUserIdDep,
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
) -> appwsrv_schema.GetCashFlowSummaryResponse:
    """Get cash flow summary by transaction category"""
    effective_to = to_time or now_utc()
    effective_from = from_time or (effective_to - timedelta(days=30))
    return appwsrv_schema.GetCashFlowSummaryResponse(
        report=generate_cash_flow_summary(
            session=db.session,
            user_account_id=current_user_id,
            from_time=effective_from,
            to_time=effective_to,
        )
    )


@router.get("/cash-flow/time-series/", operation_id="get_user_account_cash_flow_time_series")
def get_cash_flow_time_series(
    current_user_id: CurrentUserIdDep,
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
    frequency: str = Query(default="monthly"),
) -> appwsrv_schema.GetCashFlowTimeSeriesResponse:
    """Get time-bucketed cash flow data"""
    effective_to = to_time or now_utc()
    effective_from = from_time or (effective_to - timedelta(days=365))
    return appwsrv_schema.GetCashFlowTimeSeriesResponse(
        report=generate_cash_flow_time_series(
            session=db.session,
            user_account_id=current_user_id,
            from_time=effective_from,
            to_time=effective_to,
            frequency=frequency,
        )
    )


@router.get("/spending/breakdown/", operation_id="get_user_account_spending_breakdown")
def get_spending_breakdown(
    current_user_id: CurrentUserIdDep,
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
) -> appwsrv_schema.GetSpendingBreakdownResponse:
    """Get spending totals grouped by PFC primary category"""
    effective_to = to_time or now_utc()
    effective_from = from_time or (effective_to - timedelta(days=30))
    return appwsrv_schema.GetSpendingBreakdownResponse(
        report=generate_spending_breakdown(
            session=db.session,
            user_account_id=current_user_id,
            from_time=effective_from,
            to_time=effective_to,
        )
    )
