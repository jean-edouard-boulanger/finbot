import calendar
from datetime import datetime, timezone
from typing import Any

from pydantic import AwareDatetime
from sqlalchemy.sql import text

from finbot.apps.appwsrv.reports.transactions import schema
from finbot.core.db.utils import row_to_dict
from finbot.model import (
    SessionType,
    SubAccountValuationHistoryEntry,
    TransactionHistoryEntry,
    TransactionMatch,
    repository,
)


def get_transactions_report(
    session: SessionType,
    user_account_id: int,
    from_time: AwareDatetime | None = None,
    to_time: AwareDatetime | None = None,
    linked_account_id: list[int] | None = None,
    transaction_type: list[str] | None = None,
    spending_category: list[str] | None = None,
    limit: int = 100,
    offset: int = 0,
) -> schema.TransactionsReport:
    settings = repository.get_user_account_settings(session, user_account_id)

    params: dict[str, Any] = {"user_account_id": user_account_id, "limit": limit, "offset": offset}

    where_clauses = [
        "la.user_account_id = :user_account_id",
        "NOT la.deleted",
    ]
    if from_time:
        params["from_time"] = from_time
        where_clauses.append("th.transaction_date >= :from_time")
    if to_time:
        params["to_time"] = to_time
        where_clauses.append("th.transaction_date <= :to_time")
    if linked_account_id:
        params["linked_account_ids"] = tuple(linked_account_id)
        where_clauses.append("th.linked_account_id IN :linked_account_ids")
    if transaction_type:
        params["transaction_types"] = tuple(transaction_type)
        where_clauses.append("th.transaction_type IN :transaction_types")
    if spending_category:
        params["spending_categories"] = tuple(spending_category)
        where_clauses.append("th.spending_category_primary IN :spending_categories")

    where = " AND ".join(where_clauses)

    count_query = f"""
        SELECT COUNT(*)
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
         WHERE {where}
    """
    total_count = session.execute(text(count_query), params).scalar() or 0

    query = f"""
        SELECT th.id,
               th.linked_account_id,
               la.account_name AS linked_account_name,
               th.sub_account_id,
               COALESCE(
                   (SELECT savhe.sub_account_description
                      FROM finbot_sub_accounts_valuation_history_entries savhe
                     WHERE savhe.linked_account_id = th.linked_account_id
                       AND savhe.sub_account_id = th.sub_account_id
                     ORDER BY savhe.history_entry_id DESC
                     LIMIT 1),
                   th.sub_account_id
               ) AS sub_account_name,
               th.transaction_date,
               th.transaction_type,
               th.amount,
               th.amount_snapshot_ccy,
               th.currency,
               th.description,
               th.symbol,
               th.units,
               th.unit_price,
               th.fee,
               th.counterparty,
               th.spending_category_primary,
               th.spending_category_detailed,
               (SELECT CASE WHEN tm.outflow_transaction_id = th.id
                       THEN tm.inflow_transaction_id
                       ELSE tm.outflow_transaction_id END
                  FROM finbot_transaction_matches tm
                 WHERE (tm.outflow_transaction_id = th.id OR tm.inflow_transaction_id = th.id)
                   AND tm.match_status != 'rejected'
                 LIMIT 1
               ) AS matched_transaction_id
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
         WHERE {where}
         ORDER BY th.transaction_date DESC
         LIMIT :limit OFFSET :offset
    """

    rows = session.execute(text(query), params)
    transactions = [schema.TransactionEntry(**row_to_dict(row)) for row in rows]

    return schema.TransactionsReport(
        valuation_ccy=settings.valuation_ccy,
        transactions=transactions,
        total_count=total_count,
    )


def serialize_transaction(
    session: SessionType,
    txn: TransactionHistoryEntry,
) -> schema.TransactionEntry:
    sub_account_name: str = (
        session.query(SubAccountValuationHistoryEntry.sub_account_description)
        .filter_by(linked_account_id=txn.linked_account_id, sub_account_id=txn.sub_account_id)
        .order_by(SubAccountValuationHistoryEntry.history_entry_id.desc())
        .limit(1)
        .scalar()  # type: ignore[no-untyped-call]
    ) or txn.sub_account_id

    match: TransactionMatch | None = (
        session.query(TransactionMatch)
        .filter(
            TransactionMatch.match_status != "rejected",
            (TransactionMatch.outflow_transaction_id == txn.id) | (TransactionMatch.inflow_transaction_id == txn.id),
        )
        .first()
    )
    matched_transaction_id = None
    if match is not None:
        matched_transaction_id = (
            match.inflow_transaction_id if match.outflow_transaction_id == txn.id else match.outflow_transaction_id
        )

    return schema.TransactionEntry(
        id=txn.id,
        linked_account_id=txn.linked_account_id,
        linked_account_name=txn.linked_account.account_name,
        sub_account_id=txn.sub_account_id,
        sub_account_name=sub_account_name,
        transaction_date=txn.transaction_date,
        transaction_type=txn.transaction_type,
        amount=float(txn.amount),
        amount_snapshot_ccy=float(txn.amount_snapshot_ccy) if txn.amount_snapshot_ccy is not None else None,
        currency=txn.currency,
        description=txn.description,
        symbol=txn.symbol,
        units=float(txn.units) if txn.units is not None else None,
        unit_price=float(txn.unit_price) if txn.unit_price is not None else None,
        fee=float(txn.fee) if txn.fee is not None else None,
        counterparty=txn.counterparty,
        spending_category_primary=txn.spending_category_primary,
        spending_category_detailed=txn.spending_category_detailed,
        matched_transaction_id=matched_transaction_id,
    )


def get_cash_flow_summary(
    session: SessionType,
    user_account_id: int,
    from_time: AwareDatetime,
    to_time: AwareDatetime,
) -> schema.CashFlowSummary:
    settings = repository.get_user_account_settings(session, user_account_id)

    query = """
        SELECT th.transaction_type,
               COALESCE(SUM(th.amount_snapshot_ccy), 0) AS total
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           AND th.transaction_date >= :from_time
           AND th.transaction_date <= :to_time
           AND th.id NOT IN (
               SELECT tm.outflow_transaction_id FROM finbot_transaction_matches tm WHERE tm.match_status != 'rejected'
               UNION ALL
               SELECT tm.inflow_transaction_id FROM finbot_transaction_matches tm WHERE tm.match_status != 'rejected'
           )
         GROUP BY th.transaction_type
         ORDER BY th.transaction_type
    """
    rows = session.execute(
        text(query),
        {"user_account_id": user_account_id, "from_time": from_time, "to_time": to_time},
    )

    by_category = []
    net = 0.0
    for row in rows:
        data = row_to_dict(row)
        total = float(data["total"])
        net += total
        by_category.append(schema.CashFlowCategoryEntry(transaction_type=data["transaction_type"], total=total))

    return schema.CashFlowSummary(
        valuation_ccy=settings.valuation_ccy,
        from_date=from_time,
        to_date=to_time,
        net_cash_flow=net,
        by_category=by_category,
    )


def get_cash_flow_time_series(
    session: SessionType,
    user_account_id: int,
    from_time: AwareDatetime,
    to_time: AwareDatetime,
    frequency: str = "monthly",
    linked_account_id: int | None = None,
) -> schema.CashFlowTimeSeries:
    settings = repository.get_user_account_settings(session, user_account_id)

    grouping = {
        "daily": "th.transaction_date::date::text",
        "weekly": "to_char(th.transaction_date, 'IYYY') || '-W' || to_char(th.transaction_date, 'IW')",
        "monthly": "to_char(th.transaction_date, 'YYYY-MM')",
    }.get(frequency, "to_char(th.transaction_date, 'YYYY-MM')")

    params: dict[str, Any] = {
        "user_account_id": user_account_id,
        "from_time": from_time,
        "to_time": to_time,
    }

    extra_where = ""
    if linked_account_id is not None:
        params["linked_account_id"] = linked_account_id
        extra_where = "AND th.linked_account_id = :linked_account_id"
        match_exclusion = """
           AND th.id NOT IN (
               SELECT tm.outflow_transaction_id
                 FROM finbot_transaction_matches tm
                 JOIN finbot_transactions_history counterpart ON counterpart.id = tm.inflow_transaction_id
                WHERE tm.match_status != 'rejected'
                  AND counterpart.linked_account_id = :linked_account_id
               UNION ALL
               SELECT tm.inflow_transaction_id
                 FROM finbot_transaction_matches tm
                 JOIN finbot_transactions_history counterpart ON counterpart.id = tm.outflow_transaction_id
                WHERE tm.match_status != 'rejected'
                  AND counterpart.linked_account_id = :linked_account_id
           )"""
    else:
        match_exclusion = """
           AND th.id NOT IN (
               SELECT tm.outflow_transaction_id FROM finbot_transaction_matches tm WHERE tm.match_status != 'rejected'
               UNION ALL
               SELECT tm.inflow_transaction_id FROM finbot_transaction_matches tm WHERE tm.match_status != 'rejected'
           )"""

    query = f"""
        SELECT {grouping} AS period,
               COALESCE(SUM(CASE WHEN th.amount_snapshot_ccy > 0 THEN th.amount_snapshot_ccy ELSE 0 END), 0) AS inflows,
               COALESCE(
                   SUM(CASE WHEN th.amount_snapshot_ccy < 0 THEN th.amount_snapshot_ccy ELSE 0 END),
                   0
               ) AS outflows,
               COALESCE(SUM(th.amount_snapshot_ccy), 0) AS net
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           AND th.transaction_date >= :from_time
           AND th.transaction_date <= :to_time
           {match_exclusion}
           {extra_where}
         GROUP BY {grouping}
         ORDER BY {grouping}
    """
    rows = session.execute(text(query), params)

    entries = [
        schema.CashFlowTimeSeriesEntry(
            period=row_to_dict(row)["period"],
            inflows=float(row_to_dict(row)["inflows"]),
            outflows=float(row_to_dict(row)["outflows"]),
            net=float(row_to_dict(row)["net"]),
        )
        for row in rows
    ]

    return schema.CashFlowTimeSeries(
        valuation_ccy=settings.valuation_ccy,
        entries=entries,
    )


def get_spending_breakdown(
    session: SessionType,
    user_account_id: int,
    from_time: AwareDatetime,
    to_time: AwareDatetime,
) -> schema.SpendingBreakdown:
    settings = repository.get_user_account_settings(session, user_account_id)

    query = """
        SELECT th.spending_category_primary AS category,
               COALESCE(SUM(ABS(th.amount_snapshot_ccy)), 0) AS total,
               COUNT(*) AS transaction_count
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           AND th.transaction_date >= :from_time
           AND th.transaction_date <= :to_time
           AND th.spending_category_primary IS NOT NULL
           AND th.transaction_type IN ('expense', 'other', 'payment')
         GROUP BY th.spending_category_primary
         ORDER BY total DESC
    """
    rows = session.execute(
        text(query),
        {"user_account_id": user_account_id, "from_time": from_time, "to_time": to_time},
    )

    entries = [
        schema.SpendingBreakdownEntry(
            category=row_to_dict(row)["category"],
            total=float(row_to_dict(row)["total"]),
            transaction_count=row_to_dict(row)["transaction_count"],
        )
        for row in rows
    ]

    return schema.SpendingBreakdown(
        valuation_ccy=settings.valuation_ccy,
        from_date=from_time,
        to_date=to_time,
        entries=entries,
    )


INCOME_TYPES = {"dividend", "interest_earned", "staking_reward", "deposit", "transfer_in"}
EXPENSE_TYPES = {
    "fee",
    "commission",
    "interest_charged",
    "tax",
    "withdrawal",
    "transfer_out",
    "payment",
    "purchase",
    "contribution",
}


def _aggregate_by_type(
    session: SessionType,
    user_account_id: int,
    from_time: datetime,
    to_time: datetime,
) -> dict[str, float]:
    query = """
        SELECT th.transaction_type,
               COALESCE(SUM(th.amount_snapshot_ccy), 0) AS total
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           AND th.transaction_date >= :from_time
           AND th.transaction_date <= :to_time
           AND th.id NOT IN (
               SELECT tm.outflow_transaction_id FROM finbot_transaction_matches tm WHERE tm.match_status != 'rejected'
               UNION ALL
               SELECT tm.inflow_transaction_id FROM finbot_transaction_matches tm WHERE tm.match_status != 'rejected'
           )
         GROUP BY th.transaction_type
    """
    rows = session.execute(
        text(query),
        {"user_account_id": user_account_id, "from_time": from_time, "to_time": to_time},
    )
    return {row_to_dict(row)["transaction_type"]: float(row_to_dict(row)["total"]) for row in rows}


def _compute_savings_entry(
    month_str: str,
    totals_by_type: dict[str, float],
    *,
    is_current: bool,
    now: datetime,
) -> schema.MonthlySavingsEntry:
    income = sum(totals_by_type.get(t, 0.0) for t in INCOME_TYPES)
    expenses = abs(sum(totals_by_type.get(t, 0.0) for t in EXPENSE_TYPES))
    savings = income - expenses
    savings_rate = savings / income if income > 0 else None

    projected_income: float | None = None
    projected_expenses: float | None = None
    projected_savings: float | None = None
    projected_savings_rate: float | None = None

    if is_current:
        day_of_month = now.day
        year, month = int(month_str[:4]), int(month_str[5:7])
        days_in_month = calendar.monthrange(year, month)[1]
        if day_of_month > 0:
            scale = days_in_month / day_of_month
            projected_income = income
            projected_expenses = expenses * scale
            projected_savings = projected_income - projected_expenses
            projected_savings_rate = projected_savings / projected_income if projected_income > 0 else None

    return schema.MonthlySavingsEntry(
        month=month_str,
        income=income,
        expenses=expenses,
        savings=savings,
        savings_rate=savings_rate,
        projected_income=projected_income,
        projected_expenses=projected_expenses,
        projected_savings=projected_savings,
        projected_savings_rate=projected_savings_rate,
    )


def get_savings_rate_report(
    session: SessionType,
    user_account_id: int,
    comparison_month: str | None = None,
) -> schema.SavingsRateReport:
    settings = repository.get_user_account_settings(session, user_account_id)
    now = datetime.now(timezone.utc)
    current_month_str = now.strftime("%Y-%m")

    if comparison_month is None:
        if now.month == 1:
            comp_year, comp_month = now.year - 1, 12
        else:
            comp_year, comp_month = now.year, now.month - 1
        comparison_month = f"{comp_year:04d}-{comp_month:02d}"

    # Current month range
    current_from = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    current_to = now

    # Comparison month range
    comp_year_int = int(comparison_month[:4])
    comp_month_int = int(comparison_month[5:7])
    comp_from = datetime(comp_year_int, comp_month_int, 1, tzinfo=timezone.utc)
    comp_last_day = calendar.monthrange(comp_year_int, comp_month_int)[1]
    comp_to = datetime(comp_year_int, comp_month_int, comp_last_day, 23, 59, 59, tzinfo=timezone.utc)

    current_totals = _aggregate_by_type(session, user_account_id, current_from, current_to)
    comp_totals = _aggregate_by_type(session, user_account_id, comp_from, comp_to)

    current_entry = _compute_savings_entry(current_month_str, current_totals, is_current=True, now=now)
    comparison_entry = _compute_savings_entry(comparison_month, comp_totals, is_current=False, now=now)

    return schema.SavingsRateReport(
        valuation_ccy=settings.valuation_ccy,
        current_month=current_entry,
        comparison_month=comparison_entry,
    )
