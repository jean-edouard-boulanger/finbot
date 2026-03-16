import asyncio
import json
import logging
from collections import defaultdict
from decimal import Decimal
from statistics import mean, stdev

from pydantic import BaseModel
from rapidfuzz import fuzz

from finbot import model
from finbot.core.description_sanitizer import sanitize_description
from finbot.core.environment import get_openai_api_key
from finbot.model import SessionType

logger = logging.getLogger(__name__)

PAYMENT_TYPES = {"payment", "purchase"}
MIN_CLUSTER_SIZE = 2
MIN_DETERMINISTIC_CLUSTER_SIZE = 3
AMOUNT_TOLERANCE_RATIO = Decimal("0.10")
AMOUNT_TOLERANCE_ABSOLUTE = Decimal("1.00")
MIN_INTERVAL_DAYS = 3
MAX_INTERVAL_DAYS = 400
MAX_CV = 0.5

# Standard intervals for 2-transaction early detection
MONTHLY_INTERVAL = (25, 35)
YEARLY_INTERVAL = (350, 380)
STANDARD_INTERVALS = [MONTHLY_INTERVAL, YEARLY_INTERVAL]

# Fuzzy description match threshold for 2-transaction pairs
DESCRIPTION_MATCH_THRESHOLD = 80

_SUBSCRIPTION_KEYWORDS = [
    # English
    "subscription",
    "subscribe",
    "recurring",
    "membership",
    "renewal",
    # French
    "abonnement",
    "cotisation",
    "renouvellement",
    "adhesion",
    "adhésion",
    # German / Dutch
    # ("abonnement" already listed above)
    # Spanish
    "suscripcion",
    "suscripción",
    # Italian
    "abbonamento",
    # Portuguese
    "assinatura",
]


def _has_subscription_keyword(description: str) -> bool:
    """Check if a raw transaction description contains a subscription keyword."""
    upper = description.upper()
    return any(kw.upper() in upper for kw in _SUBSCRIPTION_KEYWORDS)


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


def _is_standard_interval(
    transactions: list[model.TransactionHistoryEntry],
) -> float | None:
    """For exactly 2 transactions, return interval_days if it matches a standard billing cycle."""
    if len(transactions) != 2:
        return None
    sorted_txns = sorted(transactions, key=lambda t: t.transaction_date)
    interval = (sorted_txns[1].transaction_date - sorted_txns[0].transaction_date).total_seconds() / 86400
    for low, high in STANDARD_INTERVALS:
        if low <= interval <= high:
            return interval
    return None


def _validate_pair(cluster: list[model.TransactionHistoryEntry]) -> bool:
    """Validate a 2-transaction cluster as likely recurring.

    Requires a standard interval AND either:
    - A subscription keyword in either description (very strong hint), OR
    - High fuzzy match between sanitized descriptions
    """
    if _is_standard_interval(cluster) is None:
        return False

    # Subscription keyword = very strong hint, auto-confirm
    if any(_has_subscription_keyword(t.description) for t in cluster):
        return True

    # Otherwise require high fuzzy match on sanitized descriptions
    sanitized = [sanitize_description(t.description) for t in cluster]
    if not all(sanitized):  # skip if sanitization returned empty
        return False
    score = fuzz.token_sort_ratio(sanitized[0], sanitized[1])
    return score >= DESCRIPTION_MATCH_THRESHOLD


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


def _create_or_update_group(
    cluster: list[model.TransactionHistoryEntry],
    merchant_id: int,
    currency: str,
    avg_interval: float,
    user_account_id: int,
    existing_groups: list[model.RecurringTransactionGroup],
    active_group_ids: set[int],
    transaction_to_group: dict[int, int],
    db_session: SessionType,
) -> tuple[model.RecurringTransactionGroup, bool]:
    """Create or update a recurring transaction group from a validated cluster.

    Returns (group, is_new) tuple.
    """
    amounts = [abs(t.amount) for t in cluster]
    avg_amount = Decimal(str(sum(amounts) / len(amounts)))
    total_spent = Decimal(str(sum(amounts)))
    sorted_cluster = sorted(cluster, key=lambda t: t.transaction_date)
    first_seen = sorted_cluster[0].transaction_date
    last_seen = sorted_cluster[-1].transaction_date

    # Try to match to an existing group
    group = _match_group_to_existing(existing_groups, merchant_id, currency, avg_amount)
    is_new = group is None

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

    return group, is_new


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
    new_groups: list[tuple[model.RecurringTransactionGroup, list[model.TransactionHistoryEntry]]] = []

    for (merchant_id, currency), txns in groups_by_key.items():
        if len(txns) < MIN_CLUSTER_SIZE:
            continue

        clusters = _cluster_by_amount(txns)

        for cluster in clusters:
            if len(cluster) < MIN_CLUSTER_SIZE:
                continue

            if len(cluster) >= MIN_DETERMINISTIC_CLUSTER_SIZE:
                # Deterministic path: 3+ transactions, use frequency validation
                avg_interval = _validate_frequency(cluster)
                if avg_interval is None:
                    continue
            else:
                # Early detection path: exactly 2 transactions
                if not _validate_pair(cluster):
                    continue
                avg_interval = _is_standard_interval(cluster)
                assert avg_interval is not None  # _validate_pair already checked this

            group, is_new = _create_or_update_group(
                cluster=cluster,
                merchant_id=merchant_id,
                currency=currency,
                avg_interval=avg_interval,
                user_account_id=user_account_id,
                existing_groups=existing_groups,
                active_group_ids=active_group_ids,
                transaction_to_group=transaction_to_group,
                db_session=db_session,
            )
            if is_new:
                new_groups.append((group, cluster))

    # Generate LLM descriptions for newly created groups
    if new_groups:
        _describe_new_groups(new_groups, db_session)

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


# --- LLM description generation ---


class GroupDescription(BaseModel, extra="forbid"):
    group_id: int
    description: str


class GroupDescriptionResponse(BaseModel, extra="forbid"):
    results: list[GroupDescription]


def _describe_new_groups(
    groups_with_txns: list[tuple[model.RecurringTransactionGroup, list[model.TransactionHistoryEntry]]],
    db_session: SessionType,
) -> None:
    """Generate LLM descriptions for newly created recurring groups (non-fatal)."""
    try:
        asyncio.run(_describe_groups_with_llm(groups_with_txns, db_session))
    except Exception:
        logger.exception("failed to generate LLM descriptions for recurring groups")


async def _describe_groups_with_llm(
    groups_with_txns: list[tuple[model.RecurringTransactionGroup, list[model.TransactionHistoryEntry]]],
    db_session: SessionType,
) -> None:
    api_key = get_openai_api_key()
    if not api_key:
        logger.info("FINBOT_OPENAI_API_KEY not set, skipping recurring group description generation")
        return

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)

    groups_data = []
    groups_by_id: dict[int, model.RecurringTransactionGroup] = {}
    for group, txns in groups_with_txns:
        merchant = db_session.query(model.Merchant).get(group.merchant_id)
        merchant_name = merchant.name if merchant else "Unknown"
        sample_descriptions = [t.description for t in txns[:2]]
        groups_data.append(
            {
                "group_id": group.id,
                "merchant_name": merchant_name,
                "currency": group.currency,
                "avg_amount": float(group.avg_amount),
                "avg_interval_days": float(group.avg_interval_days),
                "transaction_count": group.transaction_count,
                "sample_transaction_descriptions": sample_descriptions,
            }
        )
        groups_by_id[group.id] = group

    prompt = f"""Generate a brief, human-readable description for each recurring payment group below.
The description should capture what the subscription/recurring payment is for (e.g. "Monthly streaming subscription",
"Annual cloud storage plan", "Monthly gym membership"). Use the sample transaction descriptions to infer the nature of
the recurring payment. Keep descriptions concise (under 10 words).

GROUPS:
{json.dumps(groups_data)}"""

    try:
        response = await client.responses.parse(
            model="gpt-5-mini",
            input=[{"role": "user", "content": prompt}],
            text_format=GroupDescriptionResponse,
        )

        parsed = response.output_parsed
        if not parsed:
            return

        for result in parsed.results:
            matched_group = groups_by_id.get(result.group_id)
            if matched_group is not None:
                matched_group.description = result.description

        logger.info(
            "LLM generated descriptions for %d/%d recurring groups",
            len(parsed.results),
            len(groups_with_txns),
        )

    except Exception:
        logger.exception("LLM recurring group description API call failed")


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
