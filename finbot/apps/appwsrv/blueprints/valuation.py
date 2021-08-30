from finbot.core.errors import InvalidUserInput, MissingUserData
from finbot.apps.appwsrv.blueprints import ACCOUNT, LINKED_ACCOUNTS
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.serialization import serialize_user_account_valuation
from finbot.apps.appwsrv import core as appwsrv_core
from finbot.core.web_service import service_endpoint, RequestContext
from finbot.core.utils import now_utc
from finbot.core import timeseries
from finbot.model import repository, SubAccountItemValuationHistoryEntry

from flask import Blueprint
from flask_jwt_extended import jwt_required

from typing import Union, Tuple, Optional
from datetime import timedelta, datetime, date
from collections import defaultdict, OrderedDict
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
    last_valuation = repository.get_last_history_entry(db_session, user_account_id)
    valuation_history = repository.get_user_account_historical_valuation(
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
    return {
        "valuation": serialize_user_account_valuation(
            last_valuation, valuation_history, sparkline_schedule
        )
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


@valuation_api.route(ACCOUNT.valuation.history(), methods=["GET"])
@jwt_required()
@service_endpoint(
    parameters={
        "from_time": {
            "type": datetime,
        },
        "to_time": {"type": datetime},
        "frequency": {
            "type": repository.ValuationFrequency.deserialize,
            "default": repository.ValuationFrequency.Daily,
        },
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

    frequency = request_context.parameters["frequency"]
    is_daily = frequency == repository.ValuationFrequency.Daily

    historical_valuation: list[
        repository.HistoricalValuationEntry
    ] = repository.get_user_account_historical_valuation(
        db_session,
        user_account_id,
        from_time=from_time,
        to_time=to_time,
        frequency=frequency,
    )

    if len(historical_valuation) == 0:
        raise MissingUserData("No valuation available for selected time range")

    return {
        "historical_valuation": {
            "valuation_ccy": settings.valuation_ccy,
            "series_data": {
                "x_axis": {
                    "type": "datetime" if is_daily else "category",
                    "categories": [
                        entry.period_end if is_daily else entry.valuation_period
                        for entry in historical_valuation
                    ],
                },
                "series": [
                    {
                        "name": "Last",
                        "data": [entry.last_value for entry in historical_valuation],
                    }
                ],
            },
        }
    }


@valuation_api.route(ACCOUNT.valuation.history.by.asset_type(), methods=["GET"])
# @jwt_required()
@service_endpoint(
    parameters={
        "from_time": {
            "type": datetime,
        },
        "to_time": {"type": datetime},
        "frequency": {
            "type": repository.ValuationFrequency.deserialize,
            "default": repository.ValuationFrequency.Daily,
        },
    }
)
def get_user_account_valuation_history_by_asset_type(
    request_context: RequestContext, user_account_id: int
):
    settings = repository.get_user_account_settings(db_session, user_account_id)
    from_time = request_context.parameters["from_time"]
    to_time = request_context.parameters["to_time"]
    if from_time and to_time and from_time >= to_time:
        raise InvalidUserInput("Start time parameter must be before end time parameter")

    frequency = request_context.parameters["frequency"]
    is_daily = frequency == repository.ValuationFrequency.Daily

    valuation_history: list[
        repository.AssetTypeHistoricalValuationEntry
    ] = repository.get_historical_valuation_by_asset_type(
        db_session,
        user_account_id,
        from_time=from_time,
        to_time=to_time,
        frequency=frequency,
    )
    if len(valuation_history) == 0:
        raise MissingUserData("No valuation available for selected time range")
    current_index = 0
    x_axis_layout: dict[Union[date, str], int] = OrderedDict()
    for entry in valuation_history:
        if entry.valuation_period not in x_axis_layout:
            x_axis_layout[entry.valuation_period] = current_index
            current_index += 1
    valuation_history_by_asset_type: dict[
        str, list[Optional[repository.HistoricalValuationEntry]]
    ] = defaultdict(lambda: [None] * len(x_axis_layout))
    for entry in valuation_history:
        entry_index = x_axis_layout[entry.valuation_period]
        valuation_history_by_asset_type[entry.asset_type][entry_index] = entry
    return {
        "historical_valuation": {
            "valuation_ccy": settings.valuation_ccy,
            "series_data": {
                "x_axis": {
                    "type": "datetime" if is_daily else "category",
                    "categories": [
                        datetime(year=period.year, month=period.month, day=period.day)
                        if isinstance(period, date)
                        else period
                        for period in x_axis_layout.keys()
                    ],
                },
                "series": [
                    {
                        "name": f"{asset_type.capitalize()} (Last)",
                        "data": [
                            (entry.last_value if entry is not None else None)
                            for entry in entries
                        ],
                    }
                    for asset_type, entries in valuation_history_by_asset_type.items()
                ],
            },
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


@valuation_api.route(LINKED_ACCOUNTS.valuation.history(), methods=["GET"])
@jwt_required()
@service_endpoint(
    parameters={
        "from_time": {
            "type": datetime,
        },
        "to_time": {"type": datetime},
        "frequency": {
            "type": repository.ValuationFrequency.deserialize,
            "default": repository.ValuationFrequency.Daily,
        },
    }
)
def get_linked_accounts_historical_valuation(
    request_context: RequestContext, user_account_id: int
):
    settings = repository.get_user_account_settings(db_session, user_account_id)
    from_time = request_context.parameters["from_time"]
    to_time = request_context.parameters["to_time"]
    if from_time and to_time and from_time >= to_time:
        raise InvalidUserInput("Start time parameter must be before end time parameter")
    frequency = request_context.parameters["frequency"]
    is_daily = frequency == repository.ValuationFrequency.Daily
    valuation_history = repository.get_historical_valuation_by_linked_account(
        session=db_session,
        user_account_id=user_account_id,
        from_time=from_time,
        to_time=to_time,
        frequency=frequency,
    )
    current_index = 0
    x_axis_layout: dict[Union[date, str], int] = OrderedDict()
    for entry in valuation_history:
        if entry.valuation_period not in x_axis_layout:
            x_axis_layout[entry.valuation_period] = current_index
            current_index += 1
    valuation_history_by_linked_account: dict[
        Tuple[int, str], list[Optional[repository.HistoricalValuationEntry]]
    ] = defaultdict(lambda: [None] * len(x_axis_layout))
    for entry in valuation_history:
        descriptor = (entry.linked_account_id, entry.linked_account_name)
        entry_index = x_axis_layout[entry.valuation_period]
        valuation_history_by_linked_account[descriptor][entry_index] = entry
    return {
        "historical_valuation": {
            "valuation_ccy": settings.valuation_ccy,
            "series_data": {
                "x_axis": {
                    "type": "datetime" if is_daily else "category",
                    "categories": [
                        datetime(year=period.year, month=period.month, day=period.day)
                        if isinstance(period, date)
                        else period
                        for period in x_axis_layout.keys()
                    ],
                },
                "series": [
                    {
                        "name": f"{account_name} (Last)",
                        "data": [
                            (entry.last_value if entry is not None else None)
                            for entry in entries
                        ],
                    }
                    for (
                        account_id,
                        account_name,
                    ), entries in valuation_history_by_linked_account.items()
                ],
            },
        }
    }
