from typing import Any

from pydantic import AwareDatetime
from sqlalchemy.sql import text

from finbot.apps.appwsrv.reports.transactions import schema
from finbot.core.db.utils import row_to_dict
from finbot.model import SessionType, repository


def get_transactions_report(
    session: SessionType,
    user_account_id: int,
    from_time: AwareDatetime | None = None,
    to_time: AwareDatetime | None = None,
    linked_account_id: int | None = None,
    transaction_type: list[str] | None = None,
    spending_category: str | None = None,
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
        params["linked_account_id"] = linked_account_id
        where_clauses.append("th.linked_account_id = :linked_account_id")
    if transaction_type:
        params["transaction_types"] = tuple(transaction_type)
        where_clauses.append("th.transaction_type IN :transaction_types")
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
           AND th.id NOT IN (
               SELECT tm.outflow_transaction_id FROM finbot_transaction_matches tm WHERE tm.match_status != 'rejected'
               UNION ALL
               SELECT tm.inflow_transaction_id FROM finbot_transaction_matches tm WHERE tm.match_status != 'rejected'
           )
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
