import logging
import re
from typing import Any, Literal, cast
from uuid import uuid4

from temporalio.client import WorkflowExecutionStatus
from temporalio.service import RPCError, RPCStatusCode

from finbot.core.jobs import JobPriority, JobSource
from finbot.core.temporal_ import GENERIC_TASK_QUEUE, get_job_priority, get_temporal_client
from finbot.workflows.user_account_valuation.schema import ValuationRequest, ValuationResponse
from finbot.workflows.user_account_valuation.workflows import UserAccountValuationWorkflow

logger = logging.getLogger(__name__)

ValuationJobStatus = Literal["running", "succeeded", "failed"]

#: `user_account_id` is embedded in the job id itself (rather than looked up some other way) so that
#: `parse_valuation_job_owner` can authoritatively answer "whose job is this" from the id alone, with no
#: extra round trip -- that is what lets the status endpoint reject a job id that does not belong to the
#: caller even if the id were somehow guessed or leaked.
_JOB_ID_PATTERN = re.compile(
    r"^valuation-refresh-(?P<job_source>[a-z]+)-(?P<user_account_id>\d+)-"
    r"(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"
)

_TERMINAL_STATUS: dict[WorkflowExecutionStatus, ValuationJobStatus] = {
    WorkflowExecutionStatus.COMPLETED: "succeeded",
    WorkflowExecutionStatus.FAILED: "failed",
    WorkflowExecutionStatus.CANCELED: "failed",
    WorkflowExecutionStatus.TERMINATED: "failed",
    WorkflowExecutionStatus.TIMED_OUT: "failed",
}


def _make_valuation_job_id(user_account_id: int, job_source: JobSource) -> str:
    return f"valuation-refresh-{job_source.value}-{user_account_id}-{uuid4()}"


def parse_valuation_job_owner(job_id: str) -> int | None:
    """Recover the `user_account_id` a valuation job id was minted for, or `None` if it does not parse.

    A job id that fails to parse is treated exactly like one that parses to someone else's account: both
    are rejected by the status endpoint. This is the only check standing between one account and another
    account's job status, so it must not be fooled by a job id that merely looks plausible.
    """
    match = _JOB_ID_PATTERN.fullmatch(job_id)
    if match is None:
        return None
    return int(match.group("user_account_id"))


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
        id=_make_valuation_job_id(request.user_account_id, job_source),
        task_queue=GENERIC_TASK_QUEUE,
        priority=get_job_priority(priority),
    )


async def kickoff_valuation(
    request: ValuationRequest,
    priority: JobPriority,
    job_source: JobSource,
    ignore_errors: bool = False,
) -> str | None:
    kwargs = _get_workflow_execution_kwargs(request=request, priority=priority, job_source=job_source)
    try:
        temporal_client = await get_temporal_client()
        await temporal_client.start_workflow(**kwargs)
    except Exception:
        logger.exception(f"Failed to trigger user account valuation {request=}")
        if not ignore_errors:
            raise
        return None
    return cast(str, kwargs["id"])


async def get_valuation_job_status(job_id: str) -> ValuationJobStatus | None:
    """Look up the status of a job started by `kickoff_valuation`, or `None` if Temporal has no record of it.

    Callers must independently verify `job_id` belongs to the requesting user (via
    `parse_valuation_job_owner`) before calling this: Temporal itself does not scope by user account.
    """
    temporal_client = await get_temporal_client()
    handle = temporal_client.get_workflow_handle(job_id)
    try:
        description = await handle.describe()
    except RPCError as e:
        if e.status == RPCStatusCode.NOT_FOUND:
            return None
        raise
    status = description.status
    if status is None or status in (WorkflowExecutionStatus.RUNNING, WorkflowExecutionStatus.CONTINUED_AS_NEW):
        return "running"
    return _TERMINAL_STATUS.get(status, "failed")


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
