import logging

from finbot.core.temporal_ import GENERIC_TASK_QUEUE, get_temporal_client, temporal_workflow_id
from finbot.model import db, repository
from finbot.workflows.user_account_valuation.schema import ValuationRequest
from finbot.workflows.user_account_valuation.workflows import UserAccountValuationWorkflow

logger = logging.getLogger(__name__)


async def trigger_valuation(user_account_id: int, linked_account_ids: list[int] | None = None) -> None:
    workflow_id = temporal_workflow_id("app.valuation.")
    logger.info(f"triggering valuation for account_id={user_account_id} {linked_account_ids=} {workflow_id=}")
    temporal_client = await get_temporal_client()
    account = repository.get_user_account(db.session, user_account_id)
    await temporal_client.start_workflow(
        UserAccountValuationWorkflow,
        ValuationRequest(
            user_account_id=account.id,
            linked_accounts=linked_account_ids,
        ),
        id=workflow_id,
        task_queue=GENERIC_TASK_QUEUE,
    )


async def try_trigger_valuation(
    user_account_id: int,
    linked_account_ids: list[int] | None = None,
) -> None:
    try:
        await trigger_valuation(user_account_id, linked_account_ids)
    except Exception as e:
        logger.warning(
            f"failed to trigger valuation for account_id={user_account_id} linked_account_ids={linked_account_ids}: {e}"
        )
