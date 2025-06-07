import logging
from datetime import timedelta

from fastapi import APIRouter

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv.reports.earnings.report import (
    generate as generate_earnings_report,
)
from finbot.apps.appwsrv.reports.holdings.report import (
    generate as generate_holdings_report,
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
