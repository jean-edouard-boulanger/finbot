from dataclasses import dataclass
from datetime import datetime, date

from finbot.model import repository, UserAccountHistoryEntry


@dataclass(frozen=True)
class AggregationDescription:
    as_str: str


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
    aggregation: AggregationDescription
    metrics: Metrics

    def serialize(self):
        return {"aggregation": self.aggregation, "metrics": self.metrics}


@dataclass
class Report:
    currency: str
    entries: list[ReportEntry]
    rollup: Metrics

    def serialize(self):
        return {
            "currency": self.currency,
            "entries": self.entries,
            "rollup": self.rollup,
        }


def _get_aggregated_metrics(entries: list[UserAccountHistoryEntry]) -> Metrics:
    first_value = float(entries[0].user_account_valuation_history_entry.valuation)
    last_value = float(entries[-1].user_account_valuation_history_entry.valuation)
    abs_change = last_value - first_value
    rel_change = abs_change / first_value
    return Metrics(
        first_date=entries[0].effective_at,
        first_value=first_value,
        last_date=entries[-1].effective_at,
        last_value=last_value,
        min_value=float(
            min(
                entry.user_account_valuation_history_entry.valuation
                for entry in entries
            )
        ),
        max_value=float(
            max(
                entry.user_account_valuation_history_entry.valuation
                for entry in entries
            )
        ),
        abs_change=abs_change,
        rel_change=rel_change,
    )


def _get_rollup_metrics(all_entries: list[ReportEntry]) -> Metrics:
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
        rel_change=rel_change,
    )


def generate(
    session, user_account_id: int, from_time: datetime, to_time: datetime
) -> Report:
    user_settings = repository.get_user_account(session, user_account_id)
    historical_valuation = repository.get_user_account_historical_valuation(
        session=session,
        user_account_id=user_account_id,
        from_time=from_time,
        to_time=to_time,
        frequency=repository.ValuationFrequency.Monthly,
    )
    entries = [
        ReportEntry(
            aggregation=AggregationDescription(
                entry.valuation_period.isoformat()
                if isinstance(entry.valuation_period, date)
                else entry.valuation_period
            ),
            metrics=Metrics(
                first_date=entry.period_start,
                first_value=entry.first_value,
                last_date=entry.period_end,
                last_value=entry.last_value,
                min_value=entry.min_value,
                max_value=entry.max_value,
                abs_change=entry.abs_change,
                rel_change=entry.rel_change,
            ),
        )
        for entry in historical_valuation
    ]
    return Report(
        currency=user_settings.settings.valuation_ccy,
        entries=list(reversed(entries)),
        rollup=_get_rollup_metrics(entries),
    )
