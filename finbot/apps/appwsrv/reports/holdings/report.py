from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, TypeAlias

from finbot import model
from finbot.apps.appwsrv.reports.holdings import schema as holdings_schema
from finbot.apps.appwsrv.serializer import serialize_valuation_change
from finbot.core import timeseries, utils
from finbot.core.db.session import Session
from finbot.model import repository

LinkedAccountIdType: TypeAlias = int
SubAccountIdType: TypeAlias = str


def extract_provider_specific_data(
    item: model.SubAccountItemValuationHistoryEntry,
) -> list[tuple[str, Any]]:
    provider_specific_data = item.provider_specific_data or {}
    return list(provider_specific_data.items())


@dataclass
class ReportData:
    valuation_currency: str
    user_account_valuation: model.UserAccountValuationHistoryEntry
    linked_accounts_valuation: list[model.LinkedAccountValuationHistoryEntry]
    sparkline_schedule: list[datetime]
    user_account_historical_valuation: list[repository.HistoricalValuationEntry]
    historical_valuation_by_linked_account: dict[
        LinkedAccountIdType, list[repository.HistoricalValuationEntry]
    ]
    mapped_sub_accounts: dict[
        LinkedAccountIdType, list[model.SubAccountValuationHistoryEntry]
    ]
    mapped_items: dict[
        tuple[LinkedAccountIdType, SubAccountIdType],
        list[model.SubAccountItemValuationHistoryEntry],
    ]


def build_sub_account_item_metadata_nodes(
    sub_account_valuation: model.SubAccountValuationHistoryEntry,
    sub_account_item_valuation: model.SubAccountItemValuationHistoryEntry,
) -> list[holdings_schema.SubAccountItemMetadataNode]:
    return [
        holdings_schema.SubAccountItemMetadataNode(label=label, value=value)
        for (label, value) in [
            (
                "Units",
                f"{sub_account_item_valuation.units:.2f}"
                if sub_account_item_valuation.units
                else None,
            ),
            (
                f"Value ({sub_account_valuation.sub_account_ccy})",
                f"{sub_account_item_valuation.valuation_sub_account_ccy:.2f}",
            ),
            (
                f"Unit value ({sub_account_valuation.sub_account_ccy})",
                f"{sub_account_item_valuation.valuation_sub_account_ccy / sub_account_item_valuation.units:.2f}"
                if sub_account_item_valuation.units
                else None,
            ),
            ("Type", sub_account_item_valuation.item_subtype),
            ("Account currency", sub_account_valuation.sub_account_ccy),
        ]
        + extract_provider_specific_data(sub_account_item_valuation)
        if value is not None
    ]


def build_sub_account_item_node(
    report_data: ReportData,
    sub_account_valuation: model.SubAccountValuationHistoryEntry,
    sub_account_item_valuation: model.SubAccountItemValuationHistoryEntry,
) -> holdings_schema.SubAccountItemNode:
    return holdings_schema.SubAccountItemNode(
        item=holdings_schema.SubAccountItemDescription(
            name=sub_account_item_valuation.name,
            type=sub_account_item_valuation.item_type.name,
            sub_type=sub_account_item_valuation.item_subtype,
            asset_class=sub_account_item_valuation.asset_class,
            asset_type=sub_account_item_valuation.asset_type,
        ),
        valuation=holdings_schema.Valuation(
            currency=report_data.valuation_currency,
            value=float(sub_account_item_valuation.valuation),
            change=serialize_valuation_change(
                sub_account_item_valuation.valuation_change
            ),
        ),
        children=build_sub_account_item_metadata_nodes(
            sub_account_valuation=sub_account_valuation,
            sub_account_item_valuation=sub_account_item_valuation,
        ),
    )


def build_sub_account_node(
    report_data: ReportData,
    linked_account: model.LinkedAccount,
    sub_account_valuation: model.SubAccountValuationHistoryEntry,
) -> holdings_schema.SubAccountNode:
    return holdings_schema.SubAccountNode(
        sub_account=holdings_schema.SubAccountDescription(
            id=sub_account_valuation.sub_account_id,
            currency=report_data.valuation_currency,
            description=sub_account_valuation.sub_account_description,
            type=sub_account_valuation.sub_account_type,
        ),
        valuation=holdings_schema.Valuation(
            currency=report_data.valuation_currency,
            value=float(sub_account_valuation.valuation),
            change=serialize_valuation_change(sub_account_valuation.valuation_change),
        ),
        children=[
            build_sub_account_item_node(
                report_data=report_data,
                sub_account_valuation=sub_account_valuation,
                sub_account_item_valuation=sub_account_item_valuation,
            )
            for sub_account_item_valuation in report_data.mapped_items.get(
                (linked_account.id, sub_account_valuation.sub_account_id), []
            )
        ],
    )


def build_linked_account_node(
    report_data: ReportData,
    linked_account_valuation: model.LinkedAccountValuationHistoryEntry,
) -> holdings_schema.LinkedAccountNode:
    return holdings_schema.LinkedAccountNode(
        linked_account=holdings_schema.LinkedAccountDescription(
            id=linked_account_valuation.linked_account_id,
            provider_id=linked_account_valuation.linked_account.provider_id,
            description=linked_account_valuation.linked_account.account_name,
        ),
        valuation=holdings_schema.ValuationWithSparkline(
            currency=report_data.valuation_currency,
            value=float(linked_account_valuation.valuation),
            change=serialize_valuation_change(
                linked_account_valuation.valuation_change
            ),
            sparkline=[
                las_v.last_value if las_v is not None else None
                for valuation_time, las_v in timeseries.schedulify(
                    report_data.sparkline_schedule,
                    report_data.historical_valuation_by_linked_account.get(
                        linked_account_valuation.linked_account_id, []
                    ),
                    lambda las_v: las_v.period_end,
                )
            ],
        ),
        children=[
            build_sub_account_node(
                report_data=report_data,
                linked_account=linked_account_valuation.linked_account,
                sub_account_valuation=sub_account_valuation,
            )
            for sub_account_valuation in report_data.mapped_sub_accounts.get(
                linked_account_valuation.linked_account_id, []
            )
        ],
    )


def build_user_account_node(report_data: ReportData) -> holdings_schema.UserAccountNode:
    return holdings_schema.UserAccountNode(
        valuation=holdings_schema.ValuationWithSparkline(
            currency=report_data.valuation_currency,
            value=float(report_data.user_account_valuation.valuation),
            change=serialize_valuation_change(
                report_data.user_account_valuation.valuation_change
            ),
            sparkline=[
                uas_v.last_value if uas_v is not None else None
                for valuation_time, uas_v in timeseries.schedulify(
                    report_data.sparkline_schedule,
                    report_data.user_account_historical_valuation,
                    lambda uas_v: uas_v.period_end,
                )
            ],
        ),
        children=[
            build_linked_account_node(report_data, linked_account_valuation)
            for linked_account_valuation in report_data.linked_accounts_valuation
            if not linked_account_valuation.linked_account.deleted
        ],
    )


def build_valuation_tree(data: ReportData) -> holdings_schema.ValuationTree:
    return holdings_schema.ValuationTree(valuation_tree=build_user_account_node(data))


def fetch_raw_report_data(
    session: Session, history_entry: model.UserAccountHistoryEntry
) -> ReportData:
    to_time = utils.now_utc()
    from_time = to_time - timedelta(days=30)
    user_account_valuation = repository.get_user_account_valuation(
        session=session, history_entry_id=history_entry.id
    )
    sub_accounts_valuation = repository.find_sub_accounts_valuation(
        session, history_entry.id
    )
    linked_accounts_historical_valuation = (
        repository.get_historical_valuation_by_linked_account(
            session=session,
            user_account_id=history_entry.user_account_id,
            from_time=from_time,
            to_time=to_time,
        )
    )
    historical_valuation_by_linked_account: dict[
        int, list[repository.HistoricalValuationEntry]
    ] = defaultdict(list)
    for entry in linked_accounts_historical_valuation:
        historical_valuation_by_linked_account[entry.linked_account_id].append(entry)
    mapped_sub_accounts: dict[
        int, list[model.SubAccountValuationHistoryEntry]
    ] = defaultdict(list)
    for sub_account in sub_accounts_valuation:
        mapped_sub_accounts[sub_account.linked_account_id].append(sub_account)
    items_valuation = repository.find_items_valuation(session, history_entry.id)
    mapped_items: dict[
        tuple[int, str], list[model.SubAccountItemValuationHistoryEntry]
    ] = defaultdict(list)
    for item in items_valuation:
        mapped_items[(item.linked_account_id, item.sub_account_id)].append(item)

    return ReportData(
        valuation_currency=(
            user_account_valuation.account_valuation_history_entry.valuation_ccy
        ),
        sparkline_schedule=timeseries.create_schedule(
            from_time=from_time,
            to_time=to_time,
            frequency=timeseries.ScheduleFrequency.Daily,
        ),
        user_account_valuation=user_account_valuation,
        user_account_historical_valuation=repository.get_user_account_historical_valuation(
            session=session,
            user_account_id=history_entry.user_account_id,
            from_time=from_time,
            to_time=to_time,
        ),
        linked_accounts_valuation=repository.find_linked_accounts_valuation(
            session=session, history_entry_id=history_entry.id
        ),
        historical_valuation_by_linked_account=historical_valuation_by_linked_account,
        mapped_sub_accounts=mapped_sub_accounts,
        mapped_items=mapped_items,
    )


def generate(
    session: Session, history_entry: model.UserAccountHistoryEntry
) -> holdings_schema.ValuationTree:
    report_data = fetch_raw_report_data(session, history_entry)
    return build_valuation_tree(report_data)
