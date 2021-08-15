from finbot.apps.appwsrv.blueprints import API_V1
from finbot.apps.appwsrv.reports import (
    holdings as holdings_report,
    earnings as earnings_report,
)
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv import repository
from finbot.core.errors import MissingUserData
from finbot.core.web_service import Route, service_endpoint, RequestContext
from finbot.core.utils import now_utc

from flask import Blueprint
from flask_jwt_extended import jwt_required

from datetime import timedelta
import logging


logger = logging.getLogger(__name__)


REPORTS: Route = API_V1.reports
reports_api = Blueprint("reports_api", __name__)


@reports_api.route(REPORTS.holdings(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_holdings_report(request_context: RequestContext):
    user_account_id = request_context.user_id
    history_entry = repository.find_last_history_entry(db_session, user_account_id)
    if not history_entry:
        raise MissingUserData("No data to report")
    return {
        "report": holdings_report.generate(
            session=db_session, history_entry=history_entry
        )
    }


@reports_api.route(REPORTS.earnings(), methods=["GET"])
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
