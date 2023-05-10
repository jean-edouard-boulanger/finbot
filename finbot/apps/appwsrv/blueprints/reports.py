import logging
from datetime import timedelta

from flask import Blueprint

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.reports.earnings.report import generate as generate_earnings_report
from finbot.apps.appwsrv.reports.holdings.report import generate as generate_holdings_report
from finbot.core.errors import MissingUserData
from finbot.core.utils import now_utc
from finbot.core.web_service import (
    get_user_account_id,
    jwt_required,
    service_endpoint,
    validate,
)
from finbot.model import repository

logger = logging.getLogger(__name__)


reports_api = Blueprint(
    name="reports_api", import_name=__name__, url_prefix=f"{API_URL_PREFIX}/reports"
)


@reports_api.route("/holdings/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_holdings_report() -> appwsrv_schema.GetHoldingsReportResponse:
    history_entry = repository.get_last_history_entry(db_session, get_user_account_id())
    if not history_entry:
        raise MissingUserData("No valuation available for selected time range")
    return appwsrv_schema.GetHoldingsReportResponse(
        report=generate_holdings_report(session=db_session, history_entry=history_entry)
    )


@reports_api.route("/earnings/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_earnings_report() -> appwsrv_schema.GetEarningsReportResponse:
    to_time = now_utc()
    return appwsrv_schema.GetEarningsReportResponse(
        report=generate_earnings_report(
            session=db_session,
            user_account_id=get_user_account_id(),
            from_time=to_time - timedelta(days=365),
            to_time=to_time,
        )
    )
