import logging
from collections import defaultdict
from decimal import Decimal
from statistics import mean, stdev

from finbot import model
from finbot.model import SessionType

logger = logging.getLogger(__name__)

PAYMENT_TYPES = {"payment", "purchase"}
MIN_CLUSTER_SIZE = 3
AMOUNT_TOLERANCE_RATIO = Decimal("0.10")
AMOUNT_TOLERANCE_ABSOLUTE = Decimal("1.00")
MIN_INTERVAL_DAYS = 3
MAX_INTERVAL_DAYS = 180
MAX_CV = 0.5


def _cluster_by_amount(
    transactions: list[model.TransactionHistoryEntry],
) -> list[list[model.TransactionHistoryEntry]]:
    """Cluster transactions by amount proximity in chronological order.

    Walks transactions by date and chains each to the previous amount,
    allowing gradual price drift (e.g. subscription price increases over
    time) while still splitting genuinely different price points.
    """
    sorted_txns = sorted(transactions, key=lambda t: t.transaction_date)
    clusters: list[list[model.TransactionHistoryEntry]] = []
    # Track the most recent amount in each cluster for chain comparison
    cluster_last_amounts: list[Decimal] = []

    for txn in sorted_txns:
        abs_amount = abs(txn.amount)
        placed = False
        for i, last_amount in enumerate(cluster_last_amounts):
            tolerance = max(last_amount * AMOUNT_TOLERANCE_RATIO, AMOUNT_TOLERANCE_ABSOLUTE)
            if abs(abs_amount - last_amount) <= tolerance:
                clusters[i].append(txn)
                cluster_last_amounts[i] = abs_amount
                placed = True
                break
        if not placed:
            clusters.append([txn])
            cluster_last_amounts.append(abs_amount)

    return clusters


def _validate_frequency(transactions: list[model.TransactionHistoryEntry]) -> float | None:
    """Validate that transactions occur at a regular frequency.

    Returns average interval in days if valid, None otherwise.
    """
    sorted_txns = sorted(transactions, key=lambda t: t.transaction_date)
    intervals = [
        (sorted_txns[i + 1].transaction_date - sorted_txns[i].transaction_date).total_seconds() / 86400
        for i in range(len(sorted_txns) - 1)
    ]

    if not intervals:
        return None

    avg_interval = mean(intervals)

    if avg_interval < MIN_INTERVAL_DAYS or avg_interval > MAX_INTERVAL_DAYS:
        return None

    if len(intervals) >= 2:
        sd = stdev(intervals)
        cv = sd / avg_interval if avg_interval > 0 else float("inf")
        if cv > MAX_CV:
            return None

    return avg_interval


def _match_group_to_existing(
    existing_groups: list[model.RecurringTransactionGroup],
    merchant_id: int,
    currency: str,
    avg_amount: Decimal,
) -> model.RecurringTransactionGroup | None:
    """Find an existing group that matches the cluster by merchant, currency, and amount proximity."""
    for group in existing_groups:
        if group.merchant_id != merchant_id or group.currency != currency:
            continue
        tolerance = max(group.avg_amount * AMOUNT_TOLERANCE_RATIO, AMOUNT_TOLERANCE_ABSOLUTE)
        if abs(avg_amount - group.avg_amount) <= tolerance:
            return group
    return None


def detect_recurring_transactions(
    user_account_id: int,
    db_session: SessionType,
) -> int:
    """Detect recurring transaction groups for a user account.

    Returns the number of active recurring groups.
    """
    # Query all payment/purchase transactions with a merchant
    all_transactions = (
        db_session.query(model.TransactionHistoryEntry)
        .join(  # type: ignore[no-untyped-call]
            model.LinkedAccount,
            model.TransactionHistoryEntry.linked_account_id == model.LinkedAccount.id,
        )
        .filter(
            model.LinkedAccount.user_account_id == user_account_id,
            model.TransactionHistoryEntry.transaction_type.in_(PAYMENT_TYPES),
            model.TransactionHistoryEntry.merchant_id.isnot(None),  # type: ignore[no-untyped-call]
        )
        .order_by(
            model.TransactionHistoryEntry.merchant_id,
            model.TransactionHistoryEntry.currency,
            model.TransactionHistoryEntry.transaction_date,
        )
        .all()
    )

    # Group by (merchant_id, currency)
    groups_by_key: dict[tuple[int, str], list[model.TransactionHistoryEntry]] = defaultdict(list)
    for txn in all_transactions:
        groups_by_key[(txn.merchant_id, txn.currency)].append(txn)

    # Load existing recurring groups for this user
    existing_groups: list[model.RecurringTransactionGroup] = (
        db_session.query(model.RecurringTransactionGroup).filter_by(user_account_id=user_account_id).all()
    )

    active_group_ids: set[int] = set()
    transaction_to_group: dict[int, int] = {}  # txn.id -> group.id

    for (merchant_id, currency), txns in groups_by_key.items():
        if len(txns) < MIN_CLUSTER_SIZE:
            continue

        clusters = _cluster_by_amount(txns)

        for cluster in clusters:
            if len(cluster) < MIN_CLUSTER_SIZE:
                continue

            avg_interval = _validate_frequency(cluster)
            if avg_interval is None:
                continue

            amounts = [abs(t.amount) for t in cluster]
            avg_amount = Decimal(str(sum(amounts) / len(amounts)))
            total_spent = Decimal(str(sum(amounts)))
            sorted_cluster = sorted(cluster, key=lambda t: t.transaction_date)
            first_seen = sorted_cluster[0].transaction_date
            last_seen = sorted_cluster[-1].transaction_date

            # Try to match to an existing group
            group = _match_group_to_existing(existing_groups, merchant_id, currency, avg_amount)

            if group is not None:
                # Update existing group
                group.avg_amount = avg_amount
                group.avg_interval_days = Decimal(str(avg_interval))
                group.transaction_count = len(cluster)
                group.total_spent = total_spent
                group.first_seen = first_seen
                group.last_seen = last_seen
            else:
                # Create new group
                group = model.RecurringTransactionGroup(
                    user_account_id=user_account_id,
                    merchant_id=merchant_id,
                    currency=currency,
                    avg_amount=avg_amount,
                    avg_interval_days=Decimal(str(avg_interval)),
                    transaction_count=len(cluster),
                    total_spent=total_spent,
                    first_seen=first_seen,
                    last_seen=last_seen,
                )
                db_session.add(group)
                db_session.flush()  # Get the id
                existing_groups.append(group)

            active_group_ids.add(group.id)
            for txn in cluster:
                transaction_to_group[txn.id] = group.id

    # Update recurring_group_id on all transactions for this user
    for txn in all_transactions:
        new_group_id = transaction_to_group.get(txn.id)
        if txn.recurring_group_id != new_group_id:
            txn.recurring_group_id = new_group_id

    # Delete orphaned groups (no longer active)
    for group in existing_groups:
        if group.id not in active_group_ids:
            db_session.delete(group)  # type: ignore[no-untyped-call]

    db_session.commit()
    return len(active_group_ids)


def backfill_recurring_transactions(db_session: SessionType) -> int:
    """Run recurring detection for all user accounts that have transaction history.

    Returns total number of recurring groups detected.
    """
    user_account_ids = (
        db_session.query(model.LinkedAccount.user_account_id)
        .join(  # type: ignore[no-untyped-call]
            model.TransactionHistoryEntry,
            model.TransactionHistoryEntry.linked_account_id == model.LinkedAccount.id,
        )
        .distinct()
        .all()
    )

    total = 0
    for (user_account_id,) in user_account_ids:
        total += detect_recurring_transactions(user_account_id, db_session)

    return total
