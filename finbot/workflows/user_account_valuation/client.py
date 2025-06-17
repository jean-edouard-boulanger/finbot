import logging
from typing import Any, cast

from finbot.core.jobs import JobPriority, JobSource
from finbot.core.temporal_ import GENERIC_TASK_QUEUE, get_job_priority, get_temporal_client, temporal_workflow_id
from finbot.workflows.user_account_valuation.schema import ValuationRequest, ValuationResponse
from finbot.workflows.user_account_valuation.workflows import UserAccountValuationWorkflow

logger = logging.getLogger(__name__)


def _get_workflow_execution_kwargs(
    request: ValuationRequest,
    priority: JobPriority,
    job_source: JobSource,
) -> dict[str, Any]:
    return dict(
        workflow=UserAccountValuationWorkflow,
        arg=ValuationRequest(
            user_account_id=request.user_account_id,
            linked_accounts=request.linked_accounts,
        ),
        id=temporal_workflow_id(f"{job_source.value}/valuation/"),
        task_queue=GENERIC_TASK_QUEUE,
        priority=get_job_priority(priority),
    )


async def kickoff_valuation(
    request: ValuationRequest,
    priority: JobPriority,
    job_source: JobSource,
    ignore_errors: bool = False,
) -> None:
    try:
        temporal_client = await get_temporal_client()
        await temporal_client.start_workflow(
            **_get_workflow_execution_kwargs(request=request, priority=priority, job_source=job_source)
        )
    except Exception:
        logger.exception(f"Failed to trigger user account valuation {request=}")
        if not ignore_errors:
            raise


async def run_valuation(
    request: ValuationRequest,
    priority: JobPriority,
    job_source: JobSource,
) -> ValuationResponse:
    temporal_client = await get_temporal_client()
    return cast(
        ValuationResponse,
        await temporal_client.execute_workflow(
            **_get_workflow_execution_kwargs(request=request, priority=priority, job_source=job_source)
        ),
    )
