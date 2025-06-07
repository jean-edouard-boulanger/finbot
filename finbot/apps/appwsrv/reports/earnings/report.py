from datetime import date, datetime

from finbot.apps.appwsrv.reports.earnings import schema as earnings_schema
from finbot.core import schema as core_schema
from finbot.model import SessionType, UserAccountHistoryEntry, repository


def _get_aggregated_metrics(
    entries: list[UserAccountHistoryEntry],
) -> earnings_schema.Metrics:
    first_value = float(entries[0].user_account_valuation_history_entry.valuation)
    last_value = float(entries[-1].user_account_valuation_history_entry.valuation)
    abs_change = last_value - first_value
    rel_change = abs_change / first_value
    return earnings_schema.Metrics(
        first_date=entries[0].effective_at,
        first_value=first_value,
        last_date=entries[-1].effective_at,
        last_value=last_value,
        min_value=float(min(entry.user_account_valuation_history_entry.valuation for entry in entries)),
        max_value=float(max(entry.user_account_valuation_history_entry.valuation for entry in entries)),
        abs_change=abs_change,
        rel_change=rel_change,
    )


def _get_rollup_metrics(
    all_entries: list[earnings_schema.ReportEntry],
) -> earnings_schema.Metrics:
    first_value = all_entries[0].metrics.first_value
    last_value = all_entries[-1].metrics.last_value
    abs_change = last_value - first_value
    rel_change = abs_change / first_value
    return earnings_schema.Metrics(
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
    session: SessionType,
    user_account_id: int,
    from_time: datetime,
    to_time: datetime,
) -> earnings_schema.EarningsReport:
    user_settings = repository.get_user_account(session, user_account_id)
    historical_valuation = repository.get_user_account_historical_valuation(
        session=session,
        user_account_id=user_account_id,
        from_time=from_time,
        to_time=to_time,
        frequency=core_schema.ValuationFrequency.Monthly,
    )
    entries = [
        earnings_schema.ReportEntry(
            aggregation=earnings_schema.AggregationDescription(
                as_str=(
                    entry.valuation_period.isoformat()
                    if isinstance(entry.valuation_period, date)
                    else entry.valuation_period
                )
            ),
            metrics=earnings_schema.Metrics(
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
    return earnings_schema.EarningsReport(
        currency=user_settings.settings.valuation_ccy,
        entries=list(reversed(entries)),
        rollup=_get_rollup_metrics(entries),
    )
