from finbot.core.errors import InvalidUserInput, MissingUserData
from finbot.apps.appwsrv.blueprints import ACCOUNT, LINKED_ACCOUNTS
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.serialization import serialize_user_account_valuation
from finbot.apps.appwsrv import repository, core as appwsrv_core
from finbot.core.web_service import service_endpoint, RequestContext
from finbot.core.utils import now_utc
from finbot.core import timeseries
from finbot.model import UserAccountHistoryEntry, SubAccountItemValuationHistoryEntry

from flask import Blueprint
from flask_jwt_extended import jwt_required

from datetime import timedelta, datetime
from collections import defaultdict
import logging


logger = logging.getLogger(__name__)


valuation_api = Blueprint("valuation_api", __name__)


@valuation_api.route(ACCOUNT.valuation.trigger(), methods=["POST"])
@jwt_required()
@service_endpoint()
def trigger_user_account_valuation(user_account_id: int):
    return appwsrv_core.trigger_valuation(user_account_id)


@valuation_api.route(ACCOUNT.valuation(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_user_account_valuation(user_account_id: int):
    to_time = now_utc()
    from_time = to_time - timedelta(days=30)
    valuation_history = repository.find_user_account_historical_valuation(
        session=db_session,
        user_account_id=user_account_id,
        from_time=from_time,
        to_time=to_time,
    )
    sparkline_schedule = timeseries.create_schedule(
        from_time=from_time,
        to_time=to_time,
        frequency=timeseries.ScheduleFrequency.Daily,
    )

    valuation = valuation_history[-1] if len(valuation_history) > 0 else None

    return {
        "valuation": serialize_user_account_valuation(
            valuation, valuation_history, sparkline_schedule
        )
        if valuation
        else None,
    }


@valuation_api.route(ACCOUNT.valuation.by.asset_type(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_user_account_valuation_by_asset_type(user_account_id: int):
    last_history_entry = repository.get_last_history_entry(db_session, user_account_id)
    items = repository.find_items_valuation(db_session, last_history_entry.id)
    valuation_ccy = repository.get_user_account_settings(
        db_session, user_account_id
    ).valuation_ccy
    valuation_by_asset_type: dict[str, float] = defaultdict(float)
    item: SubAccountItemValuationHistoryEntry
    for item in items:
        valuation_by_asset_type[item.item_subtype] += float(item.valuation)
    return {
        "valuation": {
            "valuation_ccy": valuation_ccy,
            "by_asset_type": valuation_by_asset_type,
        }
    }


@valuation_api.route(ACCOUNT.history(), methods=["GET"])
@jwt_required()
@service_endpoint(
    parameters={
        "from_time": {
            "type": datetime,
        },
        "to_time": {"type": datetime},
    }
)
def get_user_account_valuation_history(
    request_context: RequestContext, user_account_id: int
):
    settings = repository.get_user_account_settings(db_session, user_account_id)
    from_time = request_context.parameters["from_time"]
    to_time = request_context.parameters["to_time"]
    if from_time and to_time and from_time >= to_time:
        raise InvalidUserInput("Start time parameter must be before end time parameter")

    history_entries: list[
        UserAccountHistoryEntry
    ] = repository.find_user_account_historical_valuation(
        db_session, user_account_id, from_time, to_time
    )

    if len(history_entries) == 0:
        raise MissingUserData("No valuation available for selected time range")

    return {
        "historical_valuation": {
            "valuation_ccy": settings.valuation_ccy,
            "entries": [
                {
                    "date": entry.effective_at,
                    "currency": entry.valuation_ccy,
                    "value": entry.user_account_valuation_history_entry.valuation,
                }
                for entry in timeseries.sample_time_series(
                    history_entries,
                    time_getter=(lambda item: item.effective_at),
                    interval=timedelta(days=1),
                )
                if entry.valuation_ccy == settings.valuation_ccy
            ],
        }
    }


@valuation_api.route(LINKED_ACCOUNTS.valuation(), methods=["GET"])
@jwt_required()
@service_endpoint()
def get_linked_accounts_valuation(user_account_id: int):
    history_entry = repository.get_last_history_entry(db_session, user_account_id)
    valuation_ccy = repository.get_user_account_settings(
        db_session, user_account_id
    ).valuation_ccy
    results = repository.find_linked_accounts_valuation(db_session, history_entry.id)
    return {
        "valuation": {
            "valuation_ccy": valuation_ccy,
            "entries": [
                {
                    "linked_account": {
                        "id": entry.linked_account.id,
                        "provider_id": entry.linked_account.provider_id,
                        "description": entry.linked_account.account_name,
                    },
                    "valuation": {
                        "date": (
                            entry.effective_snapshot.effective_at
                            if entry.effective_snapshot
                            else history_entry.effective_at
                        ),
                        "currency": history_entry.valuation_ccy,
                        "value": entry.valuation,
                        "change": entry.valuation_change,
                    },
                }
                for entry in results
                if not entry.linked_account.deleted
            ],
        }
    }
