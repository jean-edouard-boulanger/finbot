"""Merchant enrichment: fuzzy matching + LLM identification.

Identifies the real merchant behind raw transaction descriptions from
depository accounts, building up a merchant database over time.
"""

import asyncio
import json
import logging
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from rapidfuzz import fuzz, process
from sqlalchemy import and_, func

from finbot import model
from finbot.core.description_sanitizer import sanitize_description
from finbot.core.environment import get_openai_api_key
from finbot.core.spending_categories import PRIMARY_CATEGORIES
from finbot.model import SessionType

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
HIGH_CONFIDENCE_THRESHOLD = 90
MEDIUM_CONFIDENCE_THRESHOLD = 60

VALID_MERCHANT_CATEGORIES: set[str] = set(PRIMARY_CATEGORIES)


class MapToExistingMerchant(BaseModel, extra="forbid"):
    """Map a transaction to an existing merchant already in the database."""

    kind: Literal["existing"] = "existing"
    transaction_id: int = Field(description="ID of the transaction being enriched")
    merchant_id: int = Field(description="ID of the matched existing merchant")


class MapToNewMerchant(BaseModel, extra="forbid"):
    """Create a new merchant and map the transaction to it."""

    kind: Literal["new"] = "new"
    transaction_id: int = Field(description="ID of the transaction being enriched")
    merchant_name: str = Field(description="Real merchant name (e.g. 'Tesco', 'Amazon')")
    merchant_description: str | None = Field(
        default=None,
        description="Brief description of what the merchant does, NOT a description of the transaction",
    )
    merchant_category: str | None = Field(
        default=None,
        description="Merchant category from the allowed list",
    )
    merchant_website_url: str | None = Field(
        default=None,
        description="Merchant website URL (e.g. 'https://www.tesco.com')",
    )


class SkipTransaction(BaseModel, extra="forbid"):
    """Skip a transaction where the counterparty is not a merchant (e.g. individual, bank transfer, salary)."""

    kind: Literal["skip"] = "skip"
    transaction_id: int = Field(description="ID of the transaction being skipped")


class MerchantEnrichmentResponse(BaseModel, extra="forbid"):
    results: list[MapToExistingMerchant | MapToNewMerchant | SkipTransaction]


def _load_merchant_patterns(
    db_session: SessionType,
) -> dict[str, tuple[int, str]]:
    """Load all merchant patterns into a dict mapping sanitized_description -> (merchant_id, merchant_name)."""
    rows = (
        db_session.query(
            model.MerchantDescriptionPattern.sanitized_description,
            model.MerchantDescriptionPattern.merchant_id,
            model.Merchant.name,
        )
        .join(model.Merchant, model.MerchantDescriptionPattern.merchant_id == model.Merchant.id)  # type: ignore[no-untyped-call]
        .all()
    )
    return {row.sanitized_description: (row.merchant_id, row.name) for row in rows}


def _get_depository_transaction_ids(
    transaction_ids: list[int],
    db_session: SessionType,
) -> list[int]:
    """Filter transaction IDs to only those from depository sub-accounts."""
    # Subquery: latest sub_account_type per (linked_account_id, sub_account_id)
    latest_type = (
        db_session.query(
            model.SubAccountValuationHistoryEntry.linked_account_id,
            model.SubAccountValuationHistoryEntry.sub_account_id,
            func.max(model.SubAccountValuationHistoryEntry.history_entry_id).label("max_hid"),
        )
        .group_by(
            model.SubAccountValuationHistoryEntry.linked_account_id,
            model.SubAccountValuationHistoryEntry.sub_account_id,
        )
        .subquery("latest_type")
    )

    depository_subs = (
        db_session.query(
            model.SubAccountValuationHistoryEntry.linked_account_id,
            model.SubAccountValuationHistoryEntry.sub_account_id,
        )
        .join(  # type: ignore[no-untyped-call]
            latest_type,
            and_(
                model.SubAccountValuationHistoryEntry.linked_account_id == latest_type.c.linked_account_id,
                model.SubAccountValuationHistoryEntry.sub_account_id == latest_type.c.sub_account_id,
                model.SubAccountValuationHistoryEntry.history_entry_id == latest_type.c.max_hid,
            ),
        )
        .filter(model.SubAccountValuationHistoryEntry.sub_account_type == "depository")
        .subquery("depository_subs")
    )

    rows = (
        db_session.query(model.TransactionHistoryEntry.id)
        .filter(model.TransactionHistoryEntry.id.in_(transaction_ids))
        .join(  # type: ignore[no-untyped-call]
            depository_subs,
            and_(
                model.TransactionHistoryEntry.linked_account_id == depository_subs.c.linked_account_id,
                model.TransactionHistoryEntry.sub_account_id == depository_subs.c.sub_account_id,
            ),
        )
        .all()
    )
    return [row.id for row in rows]


async def enrich_transactions_with_merchants(
    transaction_ids: list[int],
    db_session: SessionType,
) -> None:
    """Enrich transactions with merchant information.

    1. Filter to depository accounts only
    2. Sanitize descriptions
    3. Fuzzy match against known patterns
    4. Fall back to LLM for unrecognized merchants
    """
    depository_ids = _get_depository_transaction_ids(transaction_ids, db_session)
    if not depository_ids:
        logger.info("no depository transactions to enrich with merchants")
        return

    entries = (
        db_session.query(model.TransactionHistoryEntry)
        .filter(model.TransactionHistoryEntry.id.in_(depository_ids))
        .all()
    )
    if not entries:
        return

    patterns = _load_merchant_patterns(db_session)
    pattern_keys = list(patterns.keys())

    # Partition by fuzzy match confidence
    high_confidence: list[tuple[model.TransactionHistoryEntry, str, int]] = []  # (entry, sanitized, merchant_id)
    medium_confidence: list[tuple[model.TransactionHistoryEntry, str, list[tuple[str, float, int]]]] = []
    low_confidence: list[tuple[model.TransactionHistoryEntry, str]] = []

    for entry in entries:
        sanitized = sanitize_description(entry.description)
        if not sanitized:
            continue

        if pattern_keys:
            match = process.extractOne(
                sanitized,
                pattern_keys,
                scorer=fuzz.token_sort_ratio,
            )
        else:
            match = None

        if match and match[1] >= HIGH_CONFIDENCE_THRESHOLD:
            merchant_id, _ = patterns[match[0]]
            high_confidence.append((entry, sanitized, merchant_id))
        elif match and match[1] >= MEDIUM_CONFIDENCE_THRESHOLD:
            # Gather top candidates for LLM
            candidates = process.extract(
                sanitized,
                pattern_keys,
                scorer=fuzz.token_sort_ratio,
                limit=5,
            )
            candidate_info = [
                (c[0], c[1], patterns[c[0]][0]) for c in candidates if c[1] >= MEDIUM_CONFIDENCE_THRESHOLD
            ]
            medium_confidence.append((entry, sanitized, candidate_info))
        else:
            low_confidence.append((entry, sanitized))

    # Process high confidence matches
    for entry, sanitized, merchant_id in high_confidence:
        entry.merchant_id = merchant_id
        _add_pattern_if_new(db_session, merchant_id, sanitized)

    logger.info(
        "merchant fuzzy match: high=%d medium=%d low=%d",
        len(high_confidence),
        len(medium_confidence),
        len(low_confidence),
    )

    # Send medium + low confidence to LLM
    llm_entries: list[tuple[model.TransactionHistoryEntry, str]] = []
    llm_candidates: dict[int, list[tuple[int, str, list[str]]]] = {}  # txn_id -> [(merchant_id, name, patterns)]

    for entry, sanitized, candidates in medium_confidence:
        llm_entries.append((entry, sanitized))
        # Build candidate info for the prompt
        merchant_candidates: list[tuple[int, str, list[str]]] = []
        seen_merchants: set[int] = set()
        for _, _, mid in candidates:
            if mid not in seen_merchants:
                seen_merchants.add(mid)
                merchant = db_session.query(model.Merchant).get(mid)
                if merchant:
                    merchant_patterns = [
                        p.sanitized_description
                        for p in db_session.query(model.MerchantDescriptionPattern)
                        .filter_by(merchant_id=mid)
                        .limit(5)
                        .all()
                    ]
                    merchant_candidates.append((mid, merchant.name, merchant_patterns))
        llm_candidates[entry.id] = merchant_candidates

    for entry, sanitized in low_confidence:
        llm_entries.append((entry, sanitized))
        llm_candidates[entry.id] = []

    if llm_entries:
        await _llm_enrich(llm_entries, llm_candidates, db_session)

    db_session.flush()


def _add_pattern_if_new(
    db_session: SessionType,
    merchant_id: int,
    sanitized_description: str,
) -> None:
    """Add a sanitized description pattern for a merchant if it doesn't already exist."""
    existing = (
        db_session.query(model.MerchantDescriptionPattern)
        .filter_by(merchant_id=merchant_id, sanitized_description=sanitized_description)
        .first()
    )
    if not existing:
        db_session.add(
            model.MerchantDescriptionPattern(
                merchant_id=merchant_id,
                sanitized_description=sanitized_description,
            )
        )
        db_session.flush()


async def _llm_enrich(
    entries: list[tuple[model.TransactionHistoryEntry, str]],
    candidates: dict[int, list[tuple[int, str, list[str]]]],
    db_session: SessionType,
) -> None:
    """Use LLM to identify merchants for transactions."""
    api_key = get_openai_api_key()
    if not api_key:
        logger.info("FINBOT_OPENAI_API_KEY not set, skipping LLM merchant enrichment")
        return

    client = AsyncOpenAI(api_key=api_key)
    semaphore = asyncio.Semaphore(8)

    batches = [entries[i : i + BATCH_SIZE] for i in range(0, len(entries), BATCH_SIZE)]
    tasks = [_llm_enrich_batch(client, batch, candidates, db_session, semaphore) for batch in batches]
    await asyncio.gather(*tasks)


async def _llm_enrich_batch(
    client: AsyncOpenAI,
    entries: list[tuple[model.TransactionHistoryEntry, str]],
    candidates: dict[int, list[tuple[int, str, list[str]]]],
    db_session: SessionType,
    semaphore: asyncio.Semaphore,
) -> None:
    """Process a batch of transactions through LLM for merchant identification."""
    entries_by_id = {entry.id: entry for entry, _ in entries}
    sanitized_by_id = {entry.id: san for entry, san in entries}

    transactions_data = []
    for entry, sanitized in entries:
        txn_data: dict[str, object] = {
            "id": entry.id,
            "original_description": entry.description,
            "sanitized_description": sanitized,
            "amount": float(entry.amount),
            "type": entry.transaction_type,
        }
        entry_candidates = candidates.get(entry.id, [])
        if entry_candidates:
            txn_data["candidate_merchants"] = [
                {
                    "merchant_id": mid,
                    "merchant_name": name,
                    "known_patterns": pats,
                }
                for mid, name, pats in entry_candidates
            ]
        transactions_data.append(txn_data)

    prompt = f"""Identify the real merchant for each transaction below.

For each transaction:
- If candidate_merchants are provided and one matches, return kind="existing" with that merchant_id
- If you can identify the merchant, return kind="new" with the real merchant name, a brief \
description of what the merchant does (NOT a description of the transaction), category, and website URL
- If the counterparty is not really a merchant (e.g. an individual person, an internal bank \
transfer, a salary payment, a government body), return kind="skip"

Be specific with merchant names (e.g. "Tesco" not "Tesco Stores", "Amazon" not "AMZN MKTP").
For website URLs, use the main domain (e.g. "https://www.tesco.com").
For merchant_category, you MUST use exactly one of these values:
{", ".join(sorted(VALID_MERCHANT_CATEGORIES))}

TRANSACTIONS:
{json.dumps(transactions_data)}"""

    async with semaphore:
        try:
            response = await client.responses.parse(
                model="gpt-5.4",
                input=[{"role": "user", "content": prompt}],
                text_format=MerchantEnrichmentResponse,
            )

            parsed = response.output_parsed
            if not parsed:
                return

            for result in parsed.results:
                if result.transaction_id not in entries_by_id:
                    logger.warning("LLM returned unknown transaction id %d, skipping", result.transaction_id)
                    continue

                entry = entries_by_id[result.transaction_id]
                matched_sanitized = sanitized_by_id.get(result.transaction_id)

                if isinstance(result, MapToExistingMerchant):
                    # Verify merchant exists
                    merchant = db_session.query(model.Merchant).get(result.merchant_id)
                    if merchant:
                        entry.merchant_id = result.merchant_id
                        if matched_sanitized:
                            _add_pattern_if_new(db_session, result.merchant_id, matched_sanitized)
                    else:
                        logger.warning("LLM referenced non-existent merchant_id %d", result.merchant_id)
                elif isinstance(result, MapToNewMerchant):
                    category = result.merchant_category
                    if category and category not in VALID_MERCHANT_CATEGORIES:
                        logger.warning(
                            "LLM returned invalid merchant category %r for transaction %d, dropping",
                            category,
                            result.transaction_id,
                        )
                        category = None

                    # Check if a merchant with this name already exists
                    existing_merchant = db_session.query(model.Merchant).filter_by(name=result.merchant_name).first()
                    if existing_merchant:
                        merchant_id = existing_merchant.id
                    else:
                        new_merchant = model.Merchant(
                            name=result.merchant_name,
                            description=result.merchant_description,
                            category=category,
                            website_url=result.merchant_website_url,
                        )
                        db_session.add(new_merchant)
                        db_session.flush()
                        merchant_id = new_merchant.id

                    entry.merchant_id = merchant_id
                    if matched_sanitized:
                        _add_pattern_if_new(db_session, merchant_id, matched_sanitized)

            logger.info("LLM enriched %d/%d transactions with merchants", len(parsed.results), len(entries))

        except Exception as e:
            logger.exception("LLM merchant enrichment API call failed: %s", e)
