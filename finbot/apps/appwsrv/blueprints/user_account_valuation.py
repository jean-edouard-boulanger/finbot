import logging
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from http import HTTPStatus
from typing import Literal, Optional, Union

from flask import Blueprint

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.core import formatting_rules
from finbot.apps.appwsrv.core import valuation as appwsrv_valuation
from finbot.apps.appwsrv.core.series import order_series_by_last_value
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.spec import spec
from finbot.core import schema as core_schema
from finbot.core import timeseries
from finbot.core.errors import InvalidUserInput, MissingUserData
from finbot.core.spec_tree import JWT_REQUIRED, ResponseSpec
from finbot.core.utils import now_utc, some
from finbot.core.web_service import jwt_required, service_endpoint
from finbot.model import (
    SubAccountItemType,
    SubAccountItemValuationHistoryEntry,
    repository,
)
from finbot.providers.schema import AssetClass, AssetType

logger = logging.getLogger(__name__)


@dataclass
class GroupValuationAgg:
    colour: core_schema.HexColour
    value: float = 0.0


user_account_valuation_api = Blueprint(
    name="user_account_valuation_api",
    import_name=__name__,
    url_prefix=f"{API_URL_PREFIX}/accounts/<int:user_account_id>/valuation",
)


ENDPOINTS_TAGS = ["User accounts (valuation)"]


@user_account_valuation_api.route("/trigger/", methods=["POST"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_202=appwsrv_schema.TriggerUserAccountValuationResponse,
    ),
    operation_id="trigger_user_account_valuation",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def trigger_user_account_valuation(
    user_account_id: int,
) -> tuple[appwsrv_schema.TriggerUserAccountValuationResponse, Literal[HTTPStatus.ACCEPTED]]:
    """Trigger user account valuation"""
    appwsrv_valuation.trigger_valuation(user_account_id)
    return appwsrv_schema.TriggerUserAccountValuationResponse(), HTTPStatus.ACCEPTED


@user_account_valuation_api.route("/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetUserAccountValuationResponse,
    ),
    operation_id="get_user_account_valuation",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_user_account_valuation(
    user_account_id: int,
) -> appwsrv_schema.GetUserAccountValuationResponse:
    """Get user account valuation"""
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
    return appwsrv_schema.GetUserAccountValuationResponse(
        valuation=appwsrv_schema.UserAccountValuation(
            date=last_valuation.effective_at,
            currency=last_valuation.valuation_ccy,
            value=float(user_account_valuation.valuation),
            total_liabilities=float(user_account_valuation.total_liabilities),
            change=serializer.serialize_valuation_change(user_account_valuation.valuation_change),
            sparkline=[
                appwsrv_schema.UserAccountValuationSparklineEntry(
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
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetUserAccountValuationByAssetTypeResponse,
    ),
    operation_id="get_user_account_valuation_by_asset_type",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_user_account_valuation_by_asset_type(
    user_account_id: int,
) -> appwsrv_schema.GetUserAccountValuationByAssetTypeResponse:
    """Get user account valuation by asset type"""
    last_history_entry = repository.get_last_history_entry(db_session, user_account_id)
    items = repository.find_items_valuation(db_session, last_history_entry.id)
    valuation_ccy = repository.get_user_account_settings(db_session, user_account_id).valuation_ccy
    valuation: dict[str, GroupValuationAgg] = {}
    item: SubAccountItemValuationHistoryEntry
    for item in items:
        if item.item_type == SubAccountItemType.Asset:
            asset_type_class_fmt = formatting_rules.get_asset_type_class_formatting_rule_by_name(
                asset_type_name=some(item.asset_type),
                asset_class_name=some(item.asset_class),
            )
            valuation.setdefault(
                asset_type_class_fmt.pretty_name,
                GroupValuationAgg(colour=asset_type_class_fmt.dominant_colour),
            ).value += float(item.valuation)
    return appwsrv_schema.GetUserAccountValuationByAssetTypeResponse(
        valuation=appwsrv_schema.ValuationByAssetType(
            valuation_ccy=valuation_ccy,
            by_asset_type=[
                appwsrv_schema.GroupValuation(
                    name=group_name,
                    value=group_valuation.value,
                    colour=group_valuation.colour,
                )
                for (group_name, group_valuation) in sorted(valuation.items(), key=lambda entry: -1.0 * entry[1].value)
                if group_valuation.value > 0.0
            ],
        )
    )


@user_account_valuation_api.route("/by/currency_exposure/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetUserAccountValuationByCurrencyExposureResponse,
    ),
    operation_id="get_user_account_valuation_by_currency_exposure",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_user_account_valuation_by_currency_exposure(
    user_account_id: int,
) -> appwsrv_schema.GetUserAccountValuationByCurrencyExposureResponse:
    """Get user account valuation by currency exposure"""
    last_history_entry = repository.get_last_history_entry(db_session, user_account_id)
    items = repository.find_items_valuation(db_session, last_history_entry.id)
    valuation_ccy = repository.get_user_account_settings(db_session, user_account_id).valuation_ccy
    valuation: dict[str, GroupValuationAgg] = {}
    for item in items:
        if item.item_type == SubAccountItemType.Asset:
            currency = item.currency
            pretty_currency_name = currency or "Unknown"
            currency_color = formatting_rules.get_currency_color(currency)
            valuation.setdefault(
                pretty_currency_name,
                GroupValuationAgg(colour=currency_color),
            ).value += float(item.valuation)
    return appwsrv_schema.GetUserAccountValuationByCurrencyExposureResponse(
        valuation=appwsrv_schema.ValuationByCurrencyExposure(
            valuation_ccy=valuation_ccy,
            by_currency_exposure=[
                appwsrv_schema.GroupValuation(
                    name=group_name,
                    value=group_valuation.value,
                    colour=group_valuation.colour,
                )
                for (group_name, group_valuation) in sorted(valuation.items(), key=lambda entry: -1.0 * entry[1].value)
                if group_valuation.value > 0.0
            ],
        )
    )


@user_account_valuation_api.route("/by/asset_class/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetUserAccountValuationByAssetClassResponse,
    ),
    operation_id="get_user_account_valuation_by_asset_class",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_user_account_valuation_by_asset_class(
    user_account_id: int,
) -> appwsrv_schema.GetUserAccountValuationByAssetClassResponse:
    """Get user account valuation by asset class"""
    last_history_entry = repository.get_last_history_entry(db_session, user_account_id)
    items = repository.find_items_valuation(db_session, last_history_entry.id)
    valuation_ccy = repository.get_user_account_settings(db_session, user_account_id).valuation_ccy
    valuation: dict[str, GroupValuationAgg] = {}
    item: SubAccountItemValuationHistoryEntry
    for item in items:
        if item.item_type == SubAccountItemType.Asset:
            asset_class_fmt = formatting_rules.get_asset_class_formatting_rule_by_name(some(item.asset_class))
            valuation.setdefault(
                asset_class_fmt.pretty_name,
                GroupValuationAgg(colour=asset_class_fmt.dominant_colour),
            ).value += float(item.valuation)
    return appwsrv_schema.GetUserAccountValuationByAssetClassResponse(
        valuation=appwsrv_schema.ValuationByAssetClass(
            valuation_ccy=valuation_ccy,
            by_asset_class=[
                appwsrv_schema.GroupValuation(
                    name=group_name,
                    value=group_valuation.value,
                    colour=group_valuation.colour,
                )
                for (group_name, group_valuation) in sorted(valuation.items(), key=lambda entry: -1.0 * entry[1].value)
                if group_valuation.value > 0.0
            ],
        )
    )


@user_account_valuation_api.route("/history/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetUserAccountValuationHistoryResponse,
    ),
    operation_id="get_user_account_historical_valuation",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_user_account_historical_valuation(
    user_account_id: int,
    query: appwsrv_schema.HistoricalValuationParams,
) -> appwsrv_schema.GetUserAccountValuationHistoryResponse:
    """Get user account valuation historical valuation"""
    settings = repository.get_user_account_settings(db_session, user_account_id)
    from_time = query.from_time
    to_time = query.to_time
    if from_time and to_time and from_time >= to_time:
        raise InvalidUserInput("Start time parameter must be before end time parameter")

    frequency = query.frequency
    is_daily = frequency == core_schema.ValuationFrequency.Daily

    historical_valuation: list[repository.HistoricalValuationEntry] = repository.get_user_account_historical_valuation(
        db_session,
        user_account_id,
        from_time=from_time,
        to_time=to_time,
        frequency=frequency,
    )

    if len(historical_valuation) == 0:
        raise MissingUserData("No valuation available for selected time range")

    return appwsrv_schema.GetUserAccountValuationHistoryResponse(
        historical_valuation=appwsrv_schema.HistoricalValuation(
            valuation_ccy=settings.valuation_ccy,
            series_data=appwsrv_schema.SeriesData(
                x_axis=appwsrv_schema.XAxisDescription(
                    type="datetime" if is_daily else "category",
                    categories=[
                        entry.period_end if is_daily else entry.valuation_period for entry in historical_valuation
                    ],
                ),
                series=[
                    appwsrv_schema.SeriesDescription(
                        name="Last",
                        data=[entry.last_value for entry in historical_valuation],
                        colour=formatting_rules.ASSETS_VALUATION_COLOUR,
                    )
                ],
            ),
        )
    )


@user_account_valuation_api.route("/history/by/asset_type/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetUserAccountValuationHistoryByAssetTypeResponse,
    ),
    operation_id="get_user_account_historical_valuation_by_asset_type",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_user_account_historical_valuation_by_asset_type(
    user_account_id: int,
    query: appwsrv_schema.HistoricalValuationParams,
) -> appwsrv_schema.GetUserAccountValuationHistoryByAssetTypeResponse:
    """Get user account valuation historical valuation by asset type"""
    settings = repository.get_user_account_settings(db_session, user_account_id)
    from_time = query.from_time
    to_time = query.to_time
    if from_time and to_time and from_time >= to_time:
        raise InvalidUserInput("Start time parameter must be before end time parameter")

    frequency = query.frequency
    is_daily = frequency == core_schema.ValuationFrequency.Daily

    valuation_history: list[repository.AssetTypeHistoricalValuationEntry] = repository.get_historical_valuation_by(
        db_session,
        user_account_id,
        by=repository.HistoricalValuationByAssetType,
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
    valuation_history_by_asset_type_class: dict[
        tuple[AssetType, AssetClass],
        list[Optional[repository.HistoricalValuationEntry]],
    ] = defaultdict(lambda: [None] * len(x_axis_layout))
    for entry in valuation_history:
        entry_index = x_axis_layout[entry.valuation_period]
        valuation_history_by_asset_type_class[(entry.asset_type, entry.asset_class)][entry_index] = entry
    return appwsrv_schema.GetUserAccountValuationHistoryByAssetTypeResponse(
        historical_valuation=appwsrv_schema.HistoricalValuation(
            valuation_ccy=settings.valuation_ccy,
            series_data=appwsrv_schema.SeriesData(
                x_axis=appwsrv_schema.XAxisDescription(
                    type="datetime" if is_daily else "category",
                    categories=[
                        datetime(year=period.year, month=period.month, day=period.day)
                        if isinstance(period, date)
                        else period
                        for period in x_axis_layout.keys()
                    ],
                ),
                series=order_series_by_last_value(
                    [
                        appwsrv_schema.SeriesDescription(
                            name=formatting_rules.get_asset_type_class_formatting_rule(
                                asset_type, asset_class
                            ).pretty_name,
                            data=[(entry.last_value if entry is not None else None) for entry in entries],
                            colour=formatting_rules.get_asset_type_class_formatting_rule(
                                asset_type, asset_class
                            ).dominant_colour,
                        )
                        for (
                            asset_type,
                            asset_class,
                        ), entries in valuation_history_by_asset_type_class.items()
                    ]
                ),
            ),
        )
    )


@user_account_valuation_api.route("/history/by/asset_class/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetUserAccountValuationHistoryByAssetClassResponse,
    ),
    operation_id="get_user_account_historical_valuation_by_asset_class",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_user_account_historical_valuation_by_asset_class(
    user_account_id: int,
    query: appwsrv_schema.HistoricalValuationParams,
) -> appwsrv_schema.GetUserAccountValuationHistoryByAssetClassResponse:
    """Get user account valuation historical valuation by asset class"""
    settings = repository.get_user_account_settings(db_session, user_account_id)
    from_time = query.from_time
    to_time = query.to_time
    if from_time and to_time and from_time >= to_time:
        raise InvalidUserInput("Start time parameter must be before end time parameter")

    frequency = query.frequency
    is_daily = frequency == core_schema.ValuationFrequency.Daily

    valuation_history: list[repository.AssetClassHistoricalValuationEntry] = repository.get_historical_valuation_by(
        db_session,
        user_account_id,
        by=repository.HistoricalValuationByAssetClass,
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
    valuation_history_by_asset_class: dict[
        AssetClass,
        list[Optional[repository.HistoricalValuationEntry]],
    ] = defaultdict(lambda: [None] * len(x_axis_layout))
    for entry in valuation_history:
        entry_index = x_axis_layout[entry.valuation_period]
        valuation_history_by_asset_class[entry.asset_class][entry_index] = entry
    return appwsrv_schema.GetUserAccountValuationHistoryByAssetClassResponse(
        historical_valuation=appwsrv_schema.HistoricalValuation(
            valuation_ccy=settings.valuation_ccy,
            series_data=appwsrv_schema.SeriesData(
                x_axis=appwsrv_schema.XAxisDescription(
                    type="datetime" if is_daily else "category",
                    categories=[
                        datetime(year=period.year, month=period.month, day=period.day)
                        if isinstance(period, date)
                        else period
                        for period in x_axis_layout.keys()
                    ],
                ),
                series=order_series_by_last_value(
                    [
                        appwsrv_schema.SeriesDescription(
                            name=formatting_rules.get_asset_class_formatting_rule(asset_class=asset_class).pretty_name,
                            data=[(entry.last_value if entry is not None else None) for entry in entries],
                            colour=formatting_rules.get_asset_class_formatting_rule(
                                asset_class=asset_class
                            ).dominant_colour,
                        )
                        for asset_class, entries in valuation_history_by_asset_class.items()
                    ]
                ),
            ),
        )
    )
