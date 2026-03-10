"""LLM-based spending categorization using OpenAI gpt-5-mini.

Categorizes transactions into the Plaid PFC taxonomy.
"""

import asyncio
import json
import logging

from openai import AsyncOpenAI
from pydantic import BaseModel

from finbot import model
from finbot.core.environment import get_openai_api_key
from finbot.core.spending_categories import PLAID_PFC_TAXONOMY, get_taxonomy_prompt_text
from finbot.model import SessionType

logger = logging.getLogger(__name__)

BATCH_SIZE = 10

VALID_CATEGORIES: set[tuple[str, str]] = {(primary, detailed) for primary, detailed, _ in PLAID_PFC_TAXONOMY}


class TransactionCategoryResult(BaseModel):
    id: int
    primary: str
    detailed: str


class CategorizeResponse(BaseModel):
    results: list[TransactionCategoryResult]


async def categorize_transaction_batch(
    transaction_ids: list[int],
    db_session: SessionType,
) -> None:
    api_key = get_openai_api_key()
    if not api_key:
        logger.info("FINBOT_OPENAI_API_KEY not set, skipping LLM spending categorization")
        return

    entries = (
        db_session.query(model.TransactionHistoryEntry)
        .filter(model.TransactionHistoryEntry.id.in_(transaction_ids))
        .all()
    )

    if not entries:
        return

    client = AsyncOpenAI(api_key=api_key)
    semaphore = asyncio.Semaphore(8)

    # Build all batch slices and launch concurrently
    batches = [entries[i : i + BATCH_SIZE] for i in range(0, len(entries), BATCH_SIZE)]
    tasks = [_categorize_batch(client, batch, db_session, semaphore) for batch in batches]
    await asyncio.gather(*tasks)


async def _categorize_batch(
    client: AsyncOpenAI,
    entries: list[model.TransactionHistoryEntry],
    db_session: SessionType,
    semaphore: asyncio.Semaphore,
) -> None:
    entries_by_id = {entry.id: entry for entry in entries}

    async with semaphore:
        categorized_ids = await _call_and_apply(client, entries, entries_by_id)

    # Retry uncategorized transactions once
    failed_ids = set(entries_by_id.keys()) - categorized_ids
    if failed_ids:
        retry_entries = [entries_by_id[eid] for eid in failed_ids]
        logger.info("Retrying %d uncategorized transactions", len(retry_entries))
        async with semaphore:
            retry_categorized = await _call_and_apply(client, retry_entries, entries_by_id)
        still_failed = failed_ids - retry_categorized
        if still_failed:
            logger.warning(
                "Failed to categorize %d transactions after retry: %s",
                len(still_failed),
                sorted(still_failed),
            )

    db_session.flush()


async def _call_and_apply(
    client: AsyncOpenAI,
    entries: list[model.TransactionHistoryEntry],
    entries_by_id: dict[int, model.TransactionHistoryEntry],
) -> set[int]:
    """Call OpenAI and apply valid results. Returns set of successfully categorized IDs."""
    taxonomy_text = get_taxonomy_prompt_text()

    transactions_json = json.dumps(
        [
            {
                "id": entry.id,
                "description": entry.description,
                "amount": float(entry.amount),
                "type": entry.transaction_type,
            }
            for entry in entries
        ]
    )

    prompt = f"""Classify each transaction into the Plaid Personal Finance Category taxonomy.

TAXONOMY REFERENCE:
{taxonomy_text}

TRANSACTIONS:
{transactions_json}

For each transaction, return the id, primary category, and detailed category."""

    try:
        response = await client.responses.parse(
            model="gpt-5-mini",
            input=[{"role": "user", "content": prompt}],
            text_format=CategorizeResponse,
        )

        parsed = response.output_parsed
        if not parsed:
            return set()

        categorized: set[int] = set()
        for cat in parsed.results:
            if cat.id not in entries_by_id:
                logger.warning("LLM returned unknown transaction id %d, skipping", cat.id)
                continue
            if (cat.primary, cat.detailed) not in VALID_CATEGORIES:
                logger.warning(
                    "LLM returned invalid category (%s, %s) for transaction %d, skipping",
                    cat.primary,
                    cat.detailed,
                    cat.id,
                )
                continue
            entry = entries_by_id[cat.id]
            entry.spending_category_primary = cat.primary
            entry.spending_category_detailed = cat.detailed
            entry.spending_category_source = "llm"
            categorized.add(cat.id)

        logger.info("LLM categorized %d/%d transactions", len(categorized), len(entries))
        return categorized

    except Exception as e:
        logger.exception("LLM categorization API call failed: %s", e)
        return set()
