"""LLM-based spending categorization using OpenAI GPT-4o-mini.

Categorizes transactions into the Plaid PFC taxonomy.
Gracefully degrades if OpenAI is unavailable.
"""

import json
import logging
import os
from dataclasses import dataclass

from finbot import model
from finbot.core.spending_categories import get_taxonomy_prompt_text
from finbot.model import SessionType

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


@dataclass
class UncategorizedTransaction:
    id: int
    description: str
    amount: float
    transaction_type: str
    counterparty: str | None


def categorize_transaction_batch(
    transaction_ids: list[int],
    db_session: SessionType,
) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.info("OPENAI_API_KEY not set, skipping LLM spending categorization")
        return

    try:
        import openai
    except ImportError:
        logger.info("openai package not installed, skipping LLM spending categorization")
        return

    # Load the uncategorized transactions
    entries = (
        db_session.query(model.TransactionHistoryEntry)
        .filter(model.TransactionHistoryEntry.id.in_(transaction_ids))
        .filter(model.TransactionHistoryEntry.spending_category_source.is_(None))
        .all()
    )

    if not entries:
        return

    client = openai.OpenAI(api_key=api_key)

    # Process in batches
    for i in range(0, len(entries), BATCH_SIZE):
        batch = entries[i : i + BATCH_SIZE]
        _categorize_batch(client, batch, db_session)


def _categorize_batch(
    client: "openai.OpenAI",  # type: ignore[name-defined]
    entries: list[model.TransactionHistoryEntry],
    db_session: SessionType,
) -> None:
    taxonomy_text = get_taxonomy_prompt_text()

    transactions_json = json.dumps(
        [
            {
                "id": entry.id,
                "description": entry.description,
                "amount": float(entry.amount),
                "type": entry.transaction_type,
                "counterparty": entry.counterparty,
            }
            for entry in entries
        ]
    )

    prompt = f"""Classify each transaction into the Plaid Personal Finance Category taxonomy.

TAXONOMY REFERENCE:
{taxonomy_text}

TRANSACTIONS:
{transactions_json}

For each transaction, return a JSON array with objects having these fields:
- "id": the transaction id
- "primary": the primary category from the taxonomy
- "detailed": the detailed category from the taxonomy

Return ONLY the JSON array, no other text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            return

        result = json.loads(content)

        # Handle both {"results": [...]} and bare [...]
        if isinstance(result, dict):
            categories = result.get("results") or result.get("categories") or result.get("transactions") or []
        elif isinstance(result, list):
            categories = result
        else:
            logger.warning("unexpected LLM response format: %s", type(result))
            return

        # Build lookup
        entries_by_id = {entry.id: entry for entry in entries}

        for cat in categories:
            entry_id = cat.get("id")
            primary = cat.get("primary")
            detailed = cat.get("detailed")
            entry = entries_by_id.get(entry_id)
            if entry and primary:
                entry.spending_category_primary = primary
                entry.spending_category_detailed = detailed
                entry.spending_category_source = "llm"

        db_session.flush()
        logger.info("LLM categorized %d transactions", len(categories))

    except Exception:
        logger.exception("LLM categorization API call failed")
