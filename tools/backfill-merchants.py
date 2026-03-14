#!/usr/bin/env python3
"""Backfill merchant enrichment for existing depository transactions.

Processes all transactions in finbot_transactions_history that have
merchant_id IS NULL and belong to depository sub-accounts. Runs the
same enrichment pipeline (fuzzy match + LLM) used in the normal
history workflow.

Usage:
    python tools/backfill-merchants.py [--batch-size 500] [--dry-run]

Environment:
    FINBOT_DB_URL              - database connection string
    FINBOT_OPENAI_API_KEY      - optional, enables LLM fallback
"""

import asyncio
import logging
import sys
from argparse import ArgumentParser

from finbot import model
from finbot.core.merchant_enricher import enrich_transactions_with_merchants
from finbot.model import ScopedSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backfill-merchants")


def get_unenriched_depository_transaction_ids(
    session: model.SessionType,
) -> list[int]:
    """Get all transaction IDs where merchant_id is NULL."""
    rows = (
        session.query(model.TransactionHistoryEntry.id)
        .filter(model.TransactionHistoryEntry.merchant_id.is_(None))
        .order_by(model.TransactionHistoryEntry.id)
        .all()
    )
    return [row.id for row in rows]


def main() -> None:
    parser = ArgumentParser(description="Backfill merchant enrichment for existing transactions")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of transaction IDs to process per batch (default: 500)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only count eligible transactions, don't enrich",
    )
    args = parser.parse_args()

    with ScopedSession() as session:
        all_ids = get_unenriched_depository_transaction_ids(session)
        logger.info("found %d transactions with merchant_id IS NULL", len(all_ids))

        if not all_ids:
            logger.info("nothing to backfill")
            return

        if args.dry_run:
            logger.info("dry run: would process %d transactions in batches of %d", len(all_ids), args.batch_size)
            return

        total_processed = 0
        for i in range(0, len(all_ids), args.batch_size):
            batch_ids = all_ids[i : i + args.batch_size]
            batch_num = i // args.batch_size + 1
            total_batches = (len(all_ids) + args.batch_size - 1) // args.batch_size

            logger.info(
                "processing batch %d/%d (%d transactions)",
                batch_num,
                total_batches,
                len(batch_ids),
            )

            try:
                asyncio.run(enrich_transactions_with_merchants(batch_ids, session))
                session.commit()
                total_processed += len(batch_ids)
                logger.info("batch %d/%d committed", batch_num, total_batches)
            except Exception:
                logger.exception("batch %d/%d failed, rolling back", batch_num, total_batches)
                session.rollback()

        logger.info("backfill complete: processed %d/%d transactions", total_processed, len(all_ids))


if __name__ == "__main__":
    sys.exit(main() or 0)
