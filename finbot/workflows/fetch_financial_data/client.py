from datetime import timedelta

from temporalio.common import RetryPolicy

from finbot.core.errors import InvalidUserInput
from finbot.core.jobs import JobPriority, JobSource
from finbot.core.temporal_ import GENERIC_TASK_QUEUE, get_job_priority, get_temporal_client, temporal_workflow_id
from finbot.workflows.fetch_financial_data.schema import ValidateCredentialsRequest
from finbot.workflows.fetch_financial_data.workflows import ValidateCredentialsWorkflow


async def validate_credentials(
    request: ValidateCredentialsRequest,
    priority: JobPriority,
    job_source: JobSource,
) -> None:
    temporal_client = await get_temporal_client()
    result = await temporal_client.execute_workflow(
        ValidateCredentialsWorkflow,
        request,
        id=temporal_workflow_id(f"{job_source.value}/validate_credentials/"),
        task_queue=GENERIC_TASK_QUEUE,
        retry_policy=RetryPolicy(
            maximum_attempts=1,
        ),
        execution_timeout=timedelta(seconds=30),
        priority=get_job_priority(priority),
    )
    if not result.valid:
        raise InvalidUserInput(f"Unable to validate provided credentials ({result.error_message})")
