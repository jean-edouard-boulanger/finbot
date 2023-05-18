from finbot.core import schema as core_schema
from finbot.tasks.base import Client, Payload, celery_app


@celery_app.task()  # type: ignore
def health_task(_: Payload) -> Payload:
    return core_schema.HealthResponse(healthy=True).dict()


client = Client[core_schema.HealthRequest, core_schema.HealthResponse](
    health_task, core_schema.HealthRequest, core_schema.HealthResponse
)
