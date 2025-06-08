import logging
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.worker import Worker

from finbot.core.temporal_ import GENERIC_TASK_QUEUE, get_temporal_client
from finbot.services.financial_data_fetcher.activities import validate_credentials
from finbot.services.financial_data_fetcher.workflows import ValidateCredentialsWorkflow


logger = logging.getLogger(__name__)


@activity.defn
async def healthcheck() -> bool:
    return True


@workflow.defn
class HealthcheckWorkflow:
    @workflow.run
    async def run(self) -> bool:
        return await workflow.execute_activity(
            healthcheck,
            start_to_close_timeout=timedelta(seconds=1.0),
        )


async def worker_main() -> None:
    client = await get_temporal_client()
    worker = Worker(
        client,
        task_queue=GENERIC_TASK_QUEUE,
        workflows=[ValidateCredentialsWorkflow, HealthcheckWorkflow],
        activities=[validate_credentials, healthcheck],
    )
    logger.info(f"Running {GENERIC_TASK_QUEUE} temporal worker ...")
    await worker.run()
