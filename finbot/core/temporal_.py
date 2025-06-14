from uuid import uuid4

from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.contrib.pydantic import pydantic_data_converter

from finbot.core.environment import get_temporal_environment

GENERIC_TASK_QUEUE = "generic"
TRY_ONCE = RetryPolicy(maximum_attempts=1)


async def get_temporal_client() -> Client:
    env = get_temporal_environment()
    return await Client.connect(
        f"{env.host}:{env.port}",
        data_converter=pydantic_data_converter,
    )


def temporal_workflow_id(prefix: str = "", suffix: str = "") -> str:
    return f"{prefix}{uuid4()}{suffix}"
