from uuid import uuid4

from temporalio.client import Client

from finbot.core.environment import get_temporal_environment

GENERIC_TASK_QUEUE = "generic"


async def get_temporal_client() -> Client:
    env = get_temporal_environment()
    return await Client.connect(f"{env.host}:{env.port}")


def temporal_workflow_id(prefix: str = "", suffix: str = "") -> str:
    return f"{prefix}{uuid4()}{suffix}"
