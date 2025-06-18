import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client as TemporalClient
from temporalio.client import ScheduleHandle
from temporalio.worker import Worker

from finbot.apps.workersrv_temporal.static_schedules import get_static_schedules
from finbot.core.environment import get_desired_log_level
from finbot.core.logging import configure_logging
from finbot.core.temporal_ import GENERIC_TASK_QUEUE, TRY_ONCE, get_temporal_client
from finbot.workflows.fetch_financial_data.activities import get_financial_data, validate_credentials
from finbot.workflows.fetch_financial_data.workflows import GetFinancialDataWorkflow, ValidateCredentialsWorkflow
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
    get_ids_of_user_accounts_that_need_valuation,
    send_error_notifications,
    send_valuation_notification,
)
from finbot.workflows.user_account_valuation.workflows import RunValuationForAllUsers, UserAccountValuationWorkflow
from finbot.workflows.write_valuation_history.activities import write_history
from finbot.workflows.write_valuation_history.workflows import WriteValuationHistoryWorkflow

DEFAULT_WORKER_THREADS = 4
STATIC_SCHEDULE_PREFIX = "static_schedule"

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


async def find_existing_schedules(client: TemporalClient) -> list[ScheduleHandle]:
    return [
        client.get_schedule_handle(schedule.id)
        async for schedule in await client.list_schedules()
        if schedule.id.startswith(STATIC_SCHEDULE_PREFIX)
    ]


async def setup_static_schedules(client: TemporalClient) -> None:
    for schedule_handle in await find_existing_schedules(client):
        logger.debug(f"deleting existing schedule: {schedule_handle.id}")
        await schedule_handle.delete()
    for spec in get_static_schedules():
        new_schedule_handle = await client.create_schedule(
            id=f"{STATIC_SCHEDULE_PREFIX}.{spec.id}",
            schedule=spec.temporal_schedule,
        )
        logger.debug(f"new schedule {new_schedule_handle.id} created")


async def worker_main() -> None:
    client = await get_temporal_client()
    worker = Worker(
        client,
        task_queue=GENERIC_TASK_QUEUE,
        workflows=[
            # workflows.fetch_financial_data
            ValidateCredentialsWorkflow,
            GetFinancialDataWorkflow,
            # workflows.write_valuation_history
            WriteValuationHistoryWorkflow,
            # workflows.user_account_snapshot
            TakeUserAccountSnapshotWorkflow,
            TakeUserAccountRawSnapshotWorkflow,
            # workflows.user_account_valuation
            UserAccountValuationWorkflow,
            RunValuationForAllUsers,
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
            get_ids_of_user_accounts_that_need_valuation,
            # apps.workersrv_temporal
            healthcheck,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=DEFAULT_WORKER_THREADS),  # TODO: config
    )
    logger.info("Setting up schedules")
    await setup_static_schedules(client)
    logger.info(f"Running {GENERIC_TASK_QUEUE} temporal worker ...")
    await worker.run()
