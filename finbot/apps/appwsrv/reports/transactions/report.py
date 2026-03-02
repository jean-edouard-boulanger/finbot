from datetime import datetime

from sqlalchemy.sql import text

from finbot.apps.appwsrv.reports.transactions import schema
from finbot.core.db.utils import row_to_dict
from finbot.model import SessionType, repository


def get_transactions_report(
    session: SessionType,
    user_account_id: int,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    linked_account_id: int | None = None,
    transaction_category: list[str] | None = None,
    spending_category: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> schema.TransactionsReport:
    settings = repository.get_user_account_settings(session, user_account_id)

    params: dict = {"user_account_id": user_account_id, "limit": limit, "offset": offset}

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
        params["linked_account_id"] = linked_account_id
        where_clauses.append("th.linked_account_id = :linked_account_id")
    if transaction_category:
        params["transaction_categories"] = tuple(transaction_category)
        where_clauses.append("th.transaction_category IN :transaction_categories")
    if spending_category:
        params["spending_category"] = spending_category
        where_clauses.append("th.spending_category_primary = :spending_category")

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
               th.transaction_date,
               th.transaction_type,
               th.transaction_category,
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
               th.spending_category_detailed
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


def get_cash_flow_summary(
    session: SessionType,
    user_account_id: int,
    from_time: datetime,
    to_time: datetime,
) -> schema.CashFlowSummary:
    settings = repository.get_user_account_settings(session, user_account_id)

    query = """
        SELECT th.transaction_category AS category,
               COALESCE(SUM(th.amount_snapshot_ccy), 0) AS total
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           AND th.transaction_date >= :from_time
           AND th.transaction_date <= :to_time
         GROUP BY th.transaction_category
         ORDER BY th.transaction_category
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
        by_category.append(schema.CashFlowCategoryEntry(category=data["category"], total=total))

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
    from_time: datetime,
    to_time: datetime,
    frequency: str = "monthly",
) -> schema.CashFlowTimeSeries:
    settings = repository.get_user_account_settings(session, user_account_id)

    grouping = {
        "daily": "th.transaction_date::date::text",
        "weekly": "'W' || to_char(th.transaction_date, 'IW IYYY')",
        "monthly": "to_char(th.transaction_date, 'YYYY-MM')",
    }.get(frequency, "to_char(th.transaction_date, 'YYYY-MM')")

    query = f"""
        SELECT {grouping} AS period,
               COALESCE(SUM(CASE WHEN th.transaction_category = 'income' THEN th.amount_snapshot_ccy ELSE 0 END), 0) AS income,
               COALESCE(SUM(CASE WHEN th.transaction_category = 'expense' THEN th.amount_snapshot_ccy ELSE 0 END), 0) AS expense,
               COALESCE(SUM(th.amount_snapshot_ccy), 0) AS net
          FROM finbot_transactions_history th
          JOIN finbot_linked_accounts la ON th.linked_account_id = la.id
         WHERE la.user_account_id = :user_account_id
           AND NOT la.deleted
           AND th.transaction_date >= :from_time
           AND th.transaction_date <= :to_time
         GROUP BY {grouping}
         ORDER BY {grouping}
    """
    rows = session.execute(
        text(query),
        {"user_account_id": user_account_id, "from_time": from_time, "to_time": to_time},
    )

    entries = [
        schema.CashFlowTimeSeriesEntry(
            period=row_to_dict(row)["period"],
            income=float(row_to_dict(row)["income"]),
            expense=float(row_to_dict(row)["expense"]),
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
    from_time: datetime,
    to_time: datetime,
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
           AND th.transaction_category IN ('expense', 'other')
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
