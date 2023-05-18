from finbot.core import schema as core_schema
from finbot.core.typing_extensions import JSONSerialized
from finbot.tasks.base import Client, celery_app


@celery_app.task()  # type: ignore
def health_task(
    _: JSONSerialized[core_schema.HealthRequest],
) -> JSONSerialized[core_schema.HealthResponse]:
    return core_schema.HealthResponse(healthy=True).dict()


client = Client[core_schema.HealthRequest, core_schema.HealthResponse](
    health_task, core_schema.HealthRequest, core_schema.HealthResponse
)
