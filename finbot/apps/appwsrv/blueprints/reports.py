import logging
from datetime import timedelta

from flask import Blueprint
from flask_jwt_extended import jwt_required

from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.reports import earnings as earnings_report
from finbot.apps.appwsrv.reports import holdings as holdings_report
from finbot.core.errors import MissingUserData
from finbot.core.utils import now_utc
from finbot.core.web_service import RequestContext, service_endpoint
from finbot.model import repository

logger = logging.getLogger(__name__)


reports_api = Blueprint(
    name="reports_api", import_name=__name__, url_prefix=f"{API_URL_PREFIX}/reports"
)


@reports_api.route("/holdings/", methods=["GET"])
@jwt_required()
@service_endpoint()
def get_holdings_report(request_context: RequestContext):
    user_account_id = request_context.user_id
    history_entry = repository.get_last_history_entry(db_session, user_account_id)
    if not history_entry:
        raise MissingUserData("No valuation available for selected time range")
    return {
        "report": holdings_report.generate(
            session=db_session, history_entry=history_entry
        )
    }


@reports_api.route("/earnings/", methods=["GET"])
@jwt_required()
@service_endpoint()
def get_earnings_report(request_context: RequestContext):
    user_account_id = request_context.user_id
    to_time = now_utc()
    return {
        "report": earnings_report.generate(
            session=db_session,
            user_account_id=user_account_id,
            from_time=to_time - timedelta(days=365),
            to_time=to_time,
        )
    }
