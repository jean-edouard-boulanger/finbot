import asyncio
import json
import logging
from datetime import timedelta
from decimal import Decimal

from finbot import model
from finbot.model import SessionType

logger = logging.getLogger(__name__)

OUTFLOW_TYPES = {"transfer_out", "withdrawal", "payment", "purchase"}
INFLOW_TYPES = {"transfer_in", "deposit"}
CANONICAL_PAIRS = {("transfer_out", "transfer_in"), ("transfer_in", "transfer_out")}
MAX_DATE_DIFF = timedelta(days=7)
AMOUNT_TOLERANCE = Decimal("0.01")

# Type alias for a scored candidate: (confidence, date_diff_secs, outflow, inflow)
Candidate = tuple[Decimal, float, model.TransactionHistoryEntry, model.TransactionHistoryEntry]


def _compute_confidence(
    outflow: model.TransactionHistoryEntry,
    inflow: model.TransactionHistoryEntry,
) -> Decimal:
    score = Decimal("0.50")
    date_diff = abs((outflow.transaction_date - inflow.transaction_date).total_seconds())
    if date_diff <= 86400:  # 1 day
        score += Decimal("0.20")
    if outflow.currency == inflow.currency:
        score += Decimal("0.15")
    if (outflow.transaction_type, inflow.transaction_type) in CANONICAL_PAIRS:
        score += Decimal("0.10")
    if outflow.counterparty and inflow.linked_account:
        if (
            inflow.linked_account.account_name
            and outflow.counterparty.lower() in inflow.linked_account.account_name.lower()
        ):
            score += Decimal("0.05")
    if inflow.counterparty and outflow.linked_account:
        if (
            outflow.linked_account.account_name
            and inflow.counterparty.lower() in outflow.linked_account.account_name.lower()
        ):
            score += Decimal("0.05")
    return min(score, Decimal("1.00"))


def _build_candidates(
    outflows: list[model.TransactionHistoryEntry],
    inflows: list[model.TransactionHistoryEntry],
) -> list[Candidate]:
    candidates: list[Candidate] = []
    for out_txn in outflows:
        for in_txn in inflows:
            if (
                out_txn.linked_account_id == in_txn.linked_account_id
                and out_txn.sub_account_id == in_txn.sub_account_id
            ):
                continue
            out_amount = abs(out_txn.amount_snapshot_ccy) if out_txn.amount_snapshot_ccy is not None else None
            in_amount = abs(in_txn.amount_snapshot_ccy) if in_txn.amount_snapshot_ccy is not None else None
            if out_amount is None or in_amount is None:
                continue
            if abs(out_amount - in_amount) > AMOUNT_TOLERANCE:
                continue
            date_diff = abs(out_txn.transaction_date - in_txn.transaction_date)
            if date_diff > MAX_DATE_DIFF:
                continue
            confidence = _compute_confidence(out_txn, in_txn)
            candidates.append((confidence, date_diff.total_seconds(), out_txn, in_txn))
    candidates.sort(key=lambda c: (-c[0], c[1]))
    return candidates


def _find_tied_candidates(
    current: Candidate,
    candidates: list[Candidate],
    matched_outflow_ids: set[int],
    matched_inflow_ids: set[int],
) -> list[Candidate]:
    """Find other candidates tied with `current` on confidence and date_diff
    that share the same outflow or inflow transaction."""
    confidence, date_diff_secs, out_txn, in_txn = current
    return [
        c
        for c in candidates
        if c != current
        and c[0] == confidence
        and c[1] == date_diff_secs
        and (c[2].id == out_txn.id or c[3].id == in_txn.id)
        and c[2].id not in matched_outflow_ids
        and c[3].id not in matched_inflow_ids
    ]


def _merge_ambiguous_groups(raw_groups: list[list[Candidate]]) -> list[list[Candidate]]:
    """Merge groups that share any outflow or inflow transaction ID (transitive closure)."""
    if not raw_groups:
        return []

    # Build union-find over group indices
    parent = list(range(len(raw_groups)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Map each transaction ID to the first group index it appeared in
    txn_to_group: dict[int, int] = {}
    for i, group in enumerate(raw_groups):
        for _, _, out_txn, in_txn in group:
            for tid in (out_txn.id, in_txn.id):
                if tid in txn_to_group:
                    union(i, txn_to_group[tid])
                else:
                    txn_to_group[tid] = i

    # Collect merged groups
    merged: dict[int, list[Candidate]] = {}
    for i, group in enumerate(raw_groups):
        root = find(i)
        merged.setdefault(root, []).extend(group)

    # Deduplicate candidates within each merged group
    result: list[list[Candidate]] = []
    for group in merged.values():
        seen: set[tuple[int, int]] = set()
        deduped: list[Candidate] = []
        for c in group:
            key = (c[2].id, c[3].id)
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        result.append(deduped)

    return result


def _resolve_with_greedy(
    candidates: list[Candidate],
    user_account_id: int,
) -> tuple[list[model.TransactionMatch], list[list[Candidate]]]:
    """Run greedy assignment, returning matches and groups of ambiguous candidates."""
    matched_outflow_ids: set[int] = set()
    matched_inflow_ids: set[int] = set()
    new_matches: list[model.TransactionMatch] = []
    raw_ambiguous_groups: list[list[Candidate]] = []
    seen_ambiguous: set[int] = set()  # outflow/inflow IDs already in an ambiguous group

    for candidate in candidates:
        confidence, date_diff_secs, out_txn, in_txn = candidate
        if out_txn.id in matched_outflow_ids or in_txn.id in matched_inflow_ids:
            continue

        # If this candidate touches an already-ambiguous ID, add it to the raw groups
        # so it gets merged later (don't skip silently)
        if out_txn.id in seen_ambiguous or in_txn.id in seen_ambiguous:
            raw_ambiguous_groups.append([candidate])
            seen_ambiguous.add(out_txn.id)
            seen_ambiguous.add(in_txn.id)
            continue

        tied = _find_tied_candidates(candidate, candidates, matched_outflow_ids, matched_inflow_ids)
        if tied:
            group = [candidate] + tied
            outflow_ids = {c[2].id for c in group}
            inflow_ids = {c[3].id for c in group}
            seen_ambiguous.update(outflow_ids)
            seen_ambiguous.update(inflow_ids)
            raw_ambiguous_groups.append(group)
            continue

        matched_outflow_ids.add(out_txn.id)
        matched_inflow_ids.add(in_txn.id)
        new_matches.append(
            model.TransactionMatch(
                user_account_id=user_account_id,
                outflow_transaction_id=out_txn.id,
                inflow_transaction_id=in_txn.id,
                match_confidence=confidence,
                match_status="auto",
            )
        )

    # Merge groups that share transaction IDs (transitive closure)
    ambiguous_groups = _merge_ambiguous_groups(raw_ambiguous_groups)

    return new_matches, ambiguous_groups


def _resolve_ambiguous_with_llm(
    ambiguous_groups: list[list[Candidate]],
    user_account_id: int,
) -> list[model.TransactionMatch]:
    """Use an LLM to disambiguate tied candidate groups."""
    from finbot.core.environment import get_openai_api_key

    api_key = get_openai_api_key()
    if not api_key:
        logger.info("FINBOT_OPENAI_API_KEY not set, skipping LLM match disambiguation")
        return []

    return asyncio.run(_resolve_ambiguous_with_llm_async(ambiguous_groups, user_account_id, api_key))


async def _resolve_ambiguous_with_llm_async(
    ambiguous_groups: list[list[Candidate]],
    user_account_id: int,
    api_key: str,
) -> list[model.TransactionMatch]:
    from openai import AsyncOpenAI
    from pydantic import BaseModel

    class MatchPair(BaseModel):
        outflow_id: int
        inflow_id: int

    class DisambiguationResponse(BaseModel):
        matches: list[MatchPair]

    client = AsyncOpenAI(api_key=api_key)
    all_matches: list[model.TransactionMatch] = []

    for group in ambiguous_groups:
        # Collect unique outflows and inflows in this group
        outflows_by_id: dict[int, model.TransactionHistoryEntry] = {}
        inflows_by_id: dict[int, model.TransactionHistoryEntry] = {}
        for _, _, out_txn, in_txn in group:
            outflows_by_id[out_txn.id] = out_txn
            inflows_by_id[in_txn.id] = in_txn

        confidence = group[0][0]  # all tied at same confidence

        outflows_json = [
            {
                "id": txn.id,
                "date": txn.transaction_date.strftime("%Y-%m-%d %H:%M"),
                "type": txn.transaction_type,
                "amount": float(txn.amount),
                "currency": txn.currency,
                "description": txn.description,
                "account": txn.linked_account.account_name if txn.linked_account else None,
                "sub_account": txn.sub_account_id,
            }
            for txn in outflows_by_id.values()
        ]
        inflows_json = [
            {
                "id": txn.id,
                "date": txn.transaction_date.strftime("%Y-%m-%d %H:%M"),
                "type": txn.transaction_type,
                "amount": float(txn.amount),
                "currency": txn.currency,
                "description": txn.description,
                "account": txn.linked_account.account_name if txn.linked_account else None,
                "sub_account": txn.sub_account_id,
            }
            for txn in inflows_by_id.values()
        ]

        prompt = f"""You are matching financial transactions. These outflows and inflows have the same amount and
similar dates, but we need to determine which outflow corresponds to which inflow based on their descriptions and other
details.

OUTFLOWS (money leaving an account):
{json.dumps(outflows_json, indent=2)}

INFLOWS (money entering an account):
{json.dumps(inflows_json, indent=2)}

Match each outflow to its corresponding inflow. Each transaction can only appear in one pair. Only return pairs you are
confident about - it's better to skip uncertain matches than to pair incorrectly."""

        try:
            response = await client.responses.parse(
                model="gpt-5-mini",
                input=[{"role": "user", "content": prompt}],
                text_format=DisambiguationResponse,
            )

            parsed = response.output_parsed
            if not parsed:
                continue

            used_outflows: set[int] = set()
            used_inflows: set[int] = set()

            for pair in parsed.matches:
                if pair.outflow_id not in outflows_by_id or pair.inflow_id not in inflows_by_id:
                    logger.warning(
                        "LLM returned unknown transaction id pair (%d, %d), skipping", pair.outflow_id, pair.inflow_id
                    )
                    continue
                if pair.outflow_id in used_outflows or pair.inflow_id in used_inflows:
                    continue
                used_outflows.add(pair.outflow_id)
                used_inflows.add(pair.inflow_id)
                all_matches.append(
                    model.TransactionMatch(
                        user_account_id=user_account_id,
                        outflow_transaction_id=pair.outflow_id,
                        inflow_transaction_id=pair.inflow_id,
                        match_confidence=confidence,
                        match_status="auto",
                    )
                )

            logger.info(
                "LLM disambiguated %d pairs from ambiguous group of %d outflows x %d inflows",
                len(used_outflows),
                len(outflows_by_id),
                len(inflows_by_id),
            )

        except Exception as e:
            logger.exception("LLM disambiguation failed for ambiguous group: %s", e)
            continue

    return all_matches


def _run_matching(
    outflows: list[model.TransactionHistoryEntry],
    inflows: list[model.TransactionHistoryEntry],
    user_account_id: int,
    db_session: SessionType,
) -> int:
    """Core matching logic shared by match_transactions and backfill."""
    if not outflows or not inflows:
        return 0

    candidates = _build_candidates(outflows, inflows)
    new_matches, ambiguous_groups = _resolve_with_greedy(candidates, user_account_id)

    if ambiguous_groups:
        logger.info(
            "%d ambiguous group(s) found, attempting LLM disambiguation",
            len(ambiguous_groups),
        )
        try:
            llm_matches = _resolve_ambiguous_with_llm(ambiguous_groups, user_account_id)
            new_matches.extend(llm_matches)
        except Exception:
            logger.exception("LLM disambiguation failed (non-fatal)")

    if new_matches:
        db_session.add_all(new_matches)
        db_session.commit()
        logger.info("created %d transaction matches for user_account_id=%d", len(new_matches), user_account_id)

    return len(new_matches)


def _query_unmatched(
    user_account_id: int,
    db_session: SessionType,
) -> tuple[list[model.TransactionHistoryEntry], list[model.TransactionHistoryEntry]]:
    already_matched_outflow = db_session.query(model.TransactionMatch.outflow_transaction_id).filter(
        model.TransactionMatch.match_status != "rejected"
    )
    already_matched_inflow = db_session.query(model.TransactionMatch.inflow_transaction_id).filter(
        model.TransactionMatch.match_status != "rejected"
    )

    base_query = (
        db_session.query(model.TransactionHistoryEntry)
        .join(  # type: ignore[no-untyped-call]
            model.LinkedAccount,
            model.TransactionHistoryEntry.linked_account_id == model.LinkedAccount.id,
        )
        .filter(model.LinkedAccount.user_account_id == user_account_id)
    )

    outflows = (
        base_query.filter(model.TransactionHistoryEntry.transaction_type.in_(OUTFLOW_TYPES))
        .filter(model.TransactionHistoryEntry.id.notin_(already_matched_outflow))
        .all()
    )

    inflows = (
        base_query.filter(model.TransactionHistoryEntry.transaction_type.in_(INFLOW_TYPES))
        .filter(model.TransactionHistoryEntry.id.notin_(already_matched_inflow))
        .all()
    )

    return outflows, inflows


def match_transactions(
    snapshot_id: int,
    db_session: SessionType,
) -> int:
    """Match outflow/inflow transaction pairs for the user account that owns the snapshot.

    Returns the number of new matches created.
    """
    snapshot: model.UserAccountSnapshot = db_session.query(model.UserAccountSnapshot).filter_by(id=snapshot_id).one()
    user_account_id = snapshot.user_account_id
    outflows, inflows = _query_unmatched(user_account_id, db_session)
    return _run_matching(outflows, inflows, user_account_id, db_session)


def backfill_matches(db_session: SessionType) -> int:
    """Run matching for all user accounts that have transaction history.

    Returns total number of new matches created.
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
        outflows, inflows = _query_unmatched(user_account_id, db_session)
        total += _run_matching(outflows, inflows, user_account_id, db_session)

    return total
