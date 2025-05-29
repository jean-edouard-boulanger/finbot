import logging
from collections import OrderedDict, defaultdict
from datetime import date, datetime
from typing import Optional, Tuple, Union

from flask import Blueprint

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.core.series import order_series_by_last_value
from finbot.apps.appwsrv.spec import spec
from finbot.core import schema as core_schema
from finbot.core.errors import InvalidUserInput
from finbot.core.spec_tree import JWT_REQUIRED, ResponseSpec
from finbot.core.utils import some
from finbot.core.web_service import jwt_required, service_endpoint
from finbot.model import repository
from finbot.model.db import db_session

logger = logging.getLogger(__name__)


linked_accounts_valuation_api = Blueprint(
    name="linked_accounts_valuation_api",
    import_name=__name__,
    url_prefix=f"{API_URL_PREFIX}/accounts/<int:user_account_id>/linked_accounts/valuation",
)


ENDPOINTS_TAGS = ["Linked accounts (valuation)"]


@linked_accounts_valuation_api.route("/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetLinkedAccountsValuationResponse,
    ),
    operation_id="get_linked_accounts_valuation",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_linked_accounts_valuation(
    user_account_id: int,
) -> appwsrv_schema.GetLinkedAccountsValuationResponse:
    """Get linked accounts valuation"""
    history_entry = repository.get_last_history_entry(
        session=db_session,
        user_account_id=user_account_id,
    )
    valuation_ccy = repository.get_user_account_settings(
        session=db_session,
        user_account_id=user_account_id,
    ).valuation_ccy
    results = repository.find_linked_accounts_valuation(db_session, history_entry.id)
    return appwsrv_schema.GetLinkedAccountsValuationResponse(
        valuation=appwsrv_schema.LinkedAccountsValuation(
            valuation_ccy=valuation_ccy,
            entries=[
                appwsrv_schema.LinkedAccountValuationEntry(
                    linked_account=appwsrv_schema.LinkedAccountValuationLinkedAccountDescription(
                        id=entry.linked_account.id,
                        provider_id=entry.linked_account.provider_id,
                        description=entry.linked_account.account_name,
                        account_colour=entry.linked_account.account_colour,
                    ),
                    valuation=appwsrv_schema.LinkedAccountValuation(
                        date=(
                            some(entry.effective_snapshot.effective_at)
                            if entry.effective_snapshot
                            else history_entry.effective_at
                        ),
                        currency=history_entry.valuation_ccy,
                        value=float(entry.valuation),
                        change=serializer.serialize_valuation_change(entry.valuation_change),
                    ),
                )
                for entry in sorted(results, key=lambda entry: -1.0 * float(entry.valuation))
                if not entry.linked_account.deleted
            ],
        )
    )


@linked_accounts_valuation_api.route("/history/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetLinkedAccountsHistoricalValuation,
    ),
    operation_id="get_linked_accounts_historical_valuation",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_linked_accounts_historical_valuation(
    user_account_id: int,
    query: appwsrv_schema.HistoricalValuationParams,
) -> appwsrv_schema.GetLinkedAccountsHistoricalValuation:
    """Get linked accounts historical valuation"""
    settings = repository.get_user_account_settings(db_session, user_account_id)
    from_time = query.from_time
    to_time = query.to_time
    if from_time and to_time and from_time >= to_time:
        raise InvalidUserInput("Start time parameter must be before end time parameter")
    frequency = query.frequency
    is_daily = frequency == core_schema.ValuationFrequency.Daily
    linked_accounts = repository.find_linked_accounts(db_session, user_account_id)
    linked_accounts_colours = {linked_account.id: linked_account.account_colour for linked_account in linked_accounts}
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
    valuation_history_by_linked_account: dict[Tuple[int, str], list[Optional[repository.HistoricalValuationEntry]]] = (
        defaultdict(lambda: [None] * len(x_axis_layout))
    )
    for entry in valuation_history:
        descriptor = (entry.linked_account_id, entry.linked_account_name)
        entry_index = x_axis_layout[entry.valuation_period]
        valuation_history_by_linked_account[descriptor][entry_index] = entry
    return appwsrv_schema.GetLinkedAccountsHistoricalValuation(
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
                            name=f"{account_name}",
                            data=[(entry.last_value if entry is not None else None) for entry in entries],
                            colour=linked_accounts_colours[account_id],
                        )
                        for (
                            account_id,
                            account_name,
                        ), entries in valuation_history_by_linked_account.items()
                    ]
                ),
            ),
        )
    )
