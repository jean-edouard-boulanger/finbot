import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.worker import Worker

from finbot.core.environment import get_desired_log_level
from finbot.core.logging import configure_logging
from finbot.core.temporal_ import GENERIC_TASK_QUEUE, TRY_ONCE, get_temporal_client
from finbot.workflows.fetch_financial_data.activities import get_financial_data, validate_credentials
from finbot.workflows.fetch_financial_data.workflows import ValidateCredentialsWorkflow
from finbot.workflows.user_account_snapshot.activities import (
    build_and_persist_final_snapshot,
    create_empty_snapshot,
    prepare_raw_snapshot_requests,
)
from finbot.workflows.user_account_snapshot.workflows import (
    TakeUserAccountRawSnapshotWorkflow,
    TakeUserAccountSnapshotWorkflow,
)
from finbot.workflows.user_account_valuation.activities import (
    send_error_notifications,
    send_valuation_notification,
)
from finbot.workflows.user_account_valuation.workflows import UserAccountValuationWorkflow
from finbot.workflows.write_valuation_history.activities import write_history
from finbot.workflows.write_valuation_history.workflows import WriteValuationHistoryWorkflow

DEFAULT_WORKER_THREADS = 4

configure_logging(get_desired_log_level())
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
            schedule_to_close_timeout=timedelta(seconds=1.0),
            retry_policy=TRY_ONCE,
        )


async def worker_main() -> None:
    client = await get_temporal_client()
    worker = Worker(
        client,
        task_queue=GENERIC_TASK_QUEUE,
        workflows=[
            # workflows.fetch_financial_data
            ValidateCredentialsWorkflow,
            # workflows.write_valuation_history
            WriteValuationHistoryWorkflow,
            # workflows.user_account_snapshot
            TakeUserAccountSnapshotWorkflow,
            TakeUserAccountRawSnapshotWorkflow,
            # workflows.user_account_valuation
            UserAccountValuationWorkflow,
            # apps.workersrv_temporal
            HealthcheckWorkflow,
        ],
        activities=[
            # workflows.fetch_financial_data
            validate_credentials,
            get_financial_data,
            # workflows.write_valuation_history
            write_history,
            # workflows.user_account_snapshot
            create_empty_snapshot,
            prepare_raw_snapshot_requests,
            build_and_persist_final_snapshot,
            # workflows.user_account_valuation
            send_error_notifications,
            send_valuation_notification,
            # apps.workersrv_temporal
            healthcheck,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=DEFAULT_WORKER_THREADS),  # TODO: config
    )
    logger.info(f"Running {GENERIC_TASK_QUEUE} temporal worker ...")
    await worker.run()
