import logging
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from typing import Optional, Union

from flask import Blueprint
from flask_jwt_extended import jwt_required
from flask_pydantic import validate

from finbot.apps.appwsrv import core as appwsrv_core
from finbot.apps.appwsrv import schema, serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.db import db_session
from finbot.core import timeseries
from finbot.core.errors import InvalidUserInput, MissingUserData
from finbot.core.utils import now_utc
from finbot.core.web_service import service_endpoint
from finbot.model import SubAccountItemValuationHistoryEntry, repository

logger = logging.getLogger(__name__)


user_account_valuation_api = Blueprint(
    name="user_account_valuation_api",
    import_name=__name__,
    url_prefix=f"{API_URL_PREFIX}/accounts/<int:user_account_id>/valuation",
)


@user_account_valuation_api.route("/trigger/", methods=["POST"])
@jwt_required()
@service_endpoint()
@validate()
def trigger_user_account_valuation(user_account_id: int):
    return appwsrv_core.trigger_valuation(user_account_id)


@user_account_valuation_api.route("/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_user_account_valuation(
    user_account_id: int,
) -> schema.GetUserAccountValuationResponse:
    to_time = now_utc()
    from_time = to_time - timedelta(days=30)
    last_valuation = repository.get_last_history_entry(db_session, user_account_id)
    user_account_valuation = last_valuation.user_account_valuation_history_entry
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
    return schema.GetUserAccountValuationResponse(
        valuation=schema.UserAccountValuation(
            date=last_valuation.effective_at,
            currency=last_valuation.valuation_ccy,
            value=user_account_valuation.valuation,
            total_liabilities=user_account_valuation.total_liabilities,
            change=serializer.serialize_valuation_change(
                user_account_valuation.valuation_change
            ),
            sparkline=[
                schema.UserAccountValuationSparklineEntry(
                    effective_at=valuation_time,
                    value=uas_v.last_value if uas_v is not None else None,
                )
                for valuation_time, uas_v in timeseries.schedulify(
                    sparkline_schedule,
                    valuation_history,
                    lambda uas_v: uas_v.period_end,
                )
            ],
        )
    )


@user_account_valuation_api.route("/by/asset_type/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
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
    return schema.GetUserAccountValuationByAssetTypeResponse(
        valuation=schema.ValuationByAssetType(
            valuation_ccy=valuation_ccy, by_asset_type=valuation_by_asset_type
        )
    )


@user_account_valuation_api.route("/history/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_user_account_valuation_history(
    user_account_id: int, query: schema.HistoricalValuationParams
) -> schema.GetUserAccountValuationHistoryResponse:
    settings = repository.get_user_account_settings(db_session, user_account_id)
    from_time = query.from_time
    to_time = query.to_time
    if from_time and to_time and from_time >= to_time:
        raise InvalidUserInput("Start time parameter must be before end time parameter")

    frequency = query.frequency
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

    return schema.GetUserAccountValuationHistoryResponse(
        historical_valuation=schema.HistoricalValuation(
            valuation_ccy=settings.valuation_ccy,
            series_data=schema.SeriesData(
                x_axis=schema.XAxisDescription(
                    type="datetime" if is_daily else "category",
                    categories=[
                        entry.period_end if is_daily else entry.valuation_period
                        for entry in historical_valuation
                    ],
                ),
                series=[
                    schema.SeriesDescription(
                        name="Last",
                        data=[entry.last_value for entry in historical_valuation],
                    )
                ],
            ),
        )
    )


@user_account_valuation_api.route("/history/by/asset_type/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_user_account_valuation_history_by_asset_type(
    user_account_id: int, query: schema.HistoricalValuationParams
) -> schema.GetUserAccountValuationHistoryByAssetTypeResponse:
    settings = repository.get_user_account_settings(db_session, user_account_id)
    from_time = query.from_time
    to_time = query.to_time
    if from_time and to_time and from_time >= to_time:
        raise InvalidUserInput("Start time parameter must be before end time parameter")

    frequency = query.frequency
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

    return schema.GetUserAccountValuationHistoryByAssetTypeResponse(
        historical_valuation=schema.HistoricalValuation(
            valuation_ccy=settings.valuation_ccy,
            series_data=schema.SeriesData(
                x_axis=schema.XAxisDescription(
                    type="datetime" if is_daily else "category",
                    categories=[
                        datetime(year=period.year, month=period.month, day=period.day)
                        if isinstance(period, date)
                        else period
                        for period in x_axis_layout.keys()
                    ],
                ),
                series=[
                    schema.SeriesDescription(
                        name=f"{asset_type.capitalize()} (Last)",
                        data=[
                            (entry.last_value if entry is not None else None)
                            for entry in entries
                        ],
                    )
                    for asset_type, entries in valuation_history_by_asset_type.items()
                ],
            ),
        )
    )
