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
    description: str | None = None,
    merchant_name: list[str] | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    amount_sign: str | None = None,
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
    if description:
        params["description_pattern"] = f"%{description}%"
        where_clauses.append("LOWER(th.description) LIKE LOWER(:description_pattern)")
    if merchant_name:
        params["merchant_names"] = tuple(merchant_name)
        where_clauses.append("m.name IN :merchant_names")
    if amount_min is not None:
        params["amount_min"] = amount_min
        where_clauses.append("ABS(th.amount) >= :amount_min")
    if amount_max is not None:
        params["amount_max"] = amount_max
        where_clauses.append("ABS(th.amount) <= :amount_max")
    if amount_sign == "credit":
        where_clauses.append("th.amount > 0")
    elif amount_sign == "debit":
        where_clauses.append("th.amount < 0")

    where = " AND ".join(where_clauses)

    merchant_join = "LEFT JOIN finbot_merchants m ON th.merchant_id = m.id" if merchant_name else ""
    count_query = f"""
        SELECT COUNT(*)
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
          {merchant_join}
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
               ) AS matched_transaction_id,
               th.merchant_id,
               m.name AS merchant_name,
               m.website_url AS merchant_website_url
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
          LEFT JOIN finbot_merchants m ON th.merchant_id = m.id
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
        merchant_id=txn.merchant_id,
        merchant_name=txn.merchant.name if txn.merchant else None,
        merchant_website_url=txn.merchant.website_url if txn.merchant else None,
    )


from finbot.core.spending_categories import PRIMARY_CATEGORY_LABELS as SPENDING_CATEGORY_LABELS


def _build_filter_where(
    params: dict[str, Any],
    *,
    from_time: AwareDatetime | None = None,
    to_time: AwareDatetime | None = None,
    linked_account_id: list[int] | None = None,
    spending_category: list[str] | None = None,
    description: str | None = None,
    merchant_name: list[str] | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    amount_sign: str | None = None,
) -> tuple[list[str], bool]:
    clauses: list[str] = []
    needs_merchant_join = False
    if from_time:
        params["f_from_time"] = from_time
        clauses.append("th.transaction_date >= :f_from_time")
    if to_time:
        params["f_to_time"] = to_time
        clauses.append("th.transaction_date <= :f_to_time")
    if linked_account_id:
        params["f_linked_account_ids"] = tuple(linked_account_id)
        clauses.append("th.linked_account_id IN :f_linked_account_ids")
    if spending_category:
        params["f_spending_categories"] = tuple(spending_category)
        clauses.append("th.spending_category_primary IN :f_spending_categories")
    if description:
        params["f_description_pattern"] = f"%{description}%"
        clauses.append("LOWER(th.description) LIKE LOWER(:f_description_pattern)")
    if merchant_name:
        params["f_merchant_names"] = tuple(merchant_name)
        clauses.append("m.name IN :f_merchant_names")
        needs_merchant_join = True
    if amount_min is not None:
        params["f_amount_min"] = amount_min
        clauses.append("ABS(th.amount) >= :f_amount_min")
    if amount_max is not None:
        params["f_amount_max"] = amount_max
        clauses.append("ABS(th.amount) <= :f_amount_max")
    if amount_sign == "credit":
        clauses.append("th.amount > 0")
    elif amount_sign == "debit":
        clauses.append("th.amount < 0")
    return clauses, needs_merchant_join


def get_transaction_filter_options(
    session: SessionType,
    user_account_id: int,
    from_time: AwareDatetime | None = None,
    to_time: AwareDatetime | None = None,
    linked_account_id: list[int] | None = None,
    spending_category: list[str] | None = None,
    description: str | None = None,
    merchant_name: list[str] | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    amount_sign: str | None = None,
) -> schema.TransactionFilterOptions:
    params: dict[str, Any] = {"user_account_id": user_account_id}
    filter_clauses, needs_merchant_join = _build_filter_where(
        params,
        from_time=from_time,
        to_time=to_time,
        linked_account_id=linked_account_id,
        spending_category=spending_category,
        description=description,
        merchant_name=merchant_name,
        amount_min=amount_min,
        amount_max=amount_max,
        amount_sign=amount_sign,
    )
    extra_where = (" AND " + " AND ".join(filter_clauses)) if filter_clauses else ""
    merchant_join = "LEFT JOIN finbot_merchants m ON th.merchant_id = m.id" if needs_merchant_join else ""

    # Accounts: all non-deleted, non-frozen accounts with filtered transaction counts
    # Filter clauses go into a subquery so accounts with 0 matching transactions still appear
    account_on_clauses = [c for c in filter_clauses if c != "th.linked_account_id IN :f_linked_account_ids"]
    account_sub_where = " AND ".join(["TRUE"] + account_on_clauses)
    account_query = f"""
        SELECT la.id, la.account_name,
               COUNT(ft.id) AS transaction_count
          FROM finbot_linked_accounts la
          LEFT JOIN (
            SELECT th.id, th.linked_account_id
              FROM finbot_transactions_history th
              {merchant_join}
             WHERE {account_sub_where}
          ) ft ON ft.linked_account_id = la.id
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           AND NOT la.frozen
         GROUP BY la.id, la.account_name
         ORDER BY COUNT(ft.id) DESC, la.account_name
    """
    account_rows = session.execute(text(account_query), params)
    accounts = [
        schema.FilterOption(
            label=row_to_dict(row)["account_name"],
            value=str(row_to_dict(row)["id"]),
            transaction_count=row_to_dict(row)["transaction_count"],
        )
        for row in account_rows
    ]

    # Merchants: only those with transactions in filtered set
    merchant_count_query = f"""
        SELECT m.name, COUNT(*) AS transaction_count
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
          JOIN finbot_merchants m ON th.merchant_id = m.id
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           {extra_where.replace("m.name IN :f_merchant_names", "TRUE")}
         GROUP BY m.name
         ORDER BY COUNT(*) DESC, m.name
    """
    merchant_rows = session.execute(text(merchant_count_query), params)
    merchants = [
        schema.FilterOption(
            label=row_to_dict(row)["name"],
            value=row_to_dict(row)["name"],
            transaction_count=row_to_dict(row)["transaction_count"],
        )
        for row in merchant_rows
    ]

    # Categories: all known categories with filtered transaction counts
    category_query = f"""
        SELECT th.spending_category_primary AS category,
               COUNT(*) AS transaction_count
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
          {merchant_join}
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           AND th.spending_category_primary IS NOT NULL
           {extra_where.replace("th.spending_category_primary IN :f_spending_categories", "TRUE")}
         GROUP BY th.spending_category_primary
    """
    category_rows = session.execute(text(category_query), params)
    category_counts: dict[str, int] = {
        row_to_dict(row)["category"]: row_to_dict(row)["transaction_count"] for row in category_rows
    }
    categories = sorted(
        [
            schema.FilterOption(
                label=label,
                value=value,
                transaction_count=category_counts.get(value, 0),
            )
            for value, label in SPENDING_CATEGORY_LABELS.items()
        ],
        key=lambda o: (-o.transaction_count, o.label),
    )

    # Amount range (filtered, excluding amount filters themselves)
    amount_extra = extra_where
    for clause in (
        "ABS(th.amount) >= :f_amount_min",
        "ABS(th.amount) <= :f_amount_max",
        "th.amount > 0",
        "th.amount < 0",
    ):
        amount_extra = amount_extra.replace(clause, "TRUE")
    amount_query = f"""
        SELECT MAX(ABS(th.amount)) AS amount_max
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
          {merchant_join}
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           {amount_extra}
    """
    amount_row = session.execute(text(amount_query), params).fetchone()
    fo_amount_min = 0.0 if amount_row and amount_row[0] is not None else None
    fo_amount_max = float(amount_row[0]) if amount_row and amount_row[0] is not None else None

    # Credit/debit counts (excluding sign filter itself)
    sign_query = f"""
        SELECT
            COUNT(*) FILTER (WHERE th.amount > 0) AS credit_count,
            COUNT(*) FILTER (WHERE th.amount < 0) AS debit_count
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
          {merchant_join}
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           {amount_extra}
    """
    sign_row = session.execute(text(sign_query), params).fetchone()
    credit_count = sign_row[0] if sign_row else 0
    debit_count = sign_row[1] if sign_row else 0

    return schema.TransactionFilterOptions(
        accounts=accounts,
        merchants=merchants,
        categories=categories,
        amount_min=fo_amount_min,
        amount_max=fo_amount_max,
        credit_count=credit_count,
        debit_count=debit_count,
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
