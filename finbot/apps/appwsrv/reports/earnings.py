from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime
import calendar

from finbot.apps.appwsrv import repository
from finbot.model import (
    UserAccountHistoryEntry
)


@dataclass(frozen=True)
class ByMonth:
    year: int
    month: int

    def serialize(self):
        return {
            "year": self.year,
            "month": self.month,
            "as_str": f"{calendar.month_name[self.month]} {self.year}"
        }


@dataclass
class Metrics:
    first_date: datetime
    first_value: float
    last_date: datetime
    last_value: float
    min_value: float
    max_value: float
    abs_change: float
    rel_change: float


@dataclass
class ReportEntry:
    aggregation: ByMonth
    metrics: Metrics

    def serialize(self):
        return {
            "aggregation": self.aggregation,
            "metrics": self.metrics
        }


@dataclass
class Report:
    currency: str
    entries: List[ReportEntry]
    rollup: Metrics

    def serialize(self):
        return {
            "currency": self.currency,
            "entries": self.entries,
            "rollup": self.rollup
        }


def _get_aggregated_metrics(entries: List[UserAccountHistoryEntry]) -> Metrics:
    first_value = float(entries[0].user_account_valuation_history_entry.valuation)
    last_value = float(entries[-1].user_account_valuation_history_entry.valuation)
    abs_change = last_value - first_value
    rel_change = abs_change / first_value
    return Metrics(
        first_date=entries[0].effective_at,
        first_value=first_value,
        last_date=entries[-1].effective_at,
        last_value=last_value,
        min_value=float(min(entry.user_account_valuation_history_entry.valuation for entry in entries)),
        max_value=float(max(entry.user_account_valuation_history_entry.valuation for entry in entries)),
        abs_change=abs_change,
        rel_change=rel_change
    )


def _get_rollup_metrics(all_entries: List[ReportEntry]) -> Metrics:
    first_value = all_entries[0].metrics.first_value
    last_value = all_entries[-1].metrics.last_value
    abs_change = last_value - first_value
    rel_change = abs_change / first_value
    return Metrics(
        first_date=all_entries[0].metrics.first_date,
        first_value=all_entries[0].metrics.first_value,
        last_date=all_entries[-1].metrics.last_date,
        last_value=all_entries[-1].metrics.last_value,
        min_value=min(entry.metrics.min_value for entry in all_entries),
        max_value=max(entry.metrics.max_value for entry in all_entries),
        abs_change=abs_change,
        rel_change=rel_change
    )


def generate(session,
             user_account_id: int,
             from_time: datetime,
             to_time: datetime) -> Report:
    user_settings = repository.get_user_account(session, user_account_id)
    historical_valuation = repository.find_user_account_historical_valuation(
        session=session,
        user_account_id=user_account_id,
        from_time=from_time,
        to_time=to_time)
    aggregated_entries = defaultdict(list)
    for entry in historical_valuation:
        agg = ByMonth(entry.effective_at.year, entry.effective_at.month)
        aggregated_entries[agg].append(entry)

    entries = [
        ReportEntry(
            aggregation=agg,
            metrics=_get_aggregated_metrics(entries)
        )
        for agg, entries in aggregated_entries.items()
    ]

    return Report(
        currency=user_settings.settings.valuation_ccy,
        entries=list(reversed(entries)),
        rollup=_get_rollup_metrics(entries)
    )
