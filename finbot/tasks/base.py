from datetime import timedelta
from typing import Any, Generic, TypeAlias, TypeVar

from celery import Celery
from celery.result import AsyncResult
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from finbot.core import environment
from finbot.core.db.session import Session
from finbot.core.logging import configure_logging
from finbot.core.schema import BaseModel

db_engine = create_engine(environment.get_database_url())
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))

FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)


celery_app = Celery("tasks", backend="rpc://", broker=FINBOT_ENV.rmq_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

RequestType = TypeVar("RequestType", bound=BaseModel)
ResponseType = TypeVar("ResponseType", bound=BaseModel)
TimeoutType: TypeAlias = int | float | timedelta


class AsyncResponse(Generic[ResponseType]):
    def __init__(self, response_type: type[ResponseType], async_result: AsyncResult):
        self._response_type = response_type
        self._async_result = async_result

    @staticmethod
    def _get_timeout_seconds(raw_timeout: TimeoutType | None) -> float | None:
        if raw_timeout is None:
            return None
        if isinstance(raw_timeout, (int, float)):
            return float(raw_timeout)
        return raw_timeout.total_seconds()

    def get(self, timeout: TimeoutType | None = None) -> ResponseType:
        return self._response_type.parse_obj(
            self._async_result.get(
                timeout=self._get_timeout_seconds(timeout),
            ),
        )


class Client(Generic[RequestType, ResponseType]):
    def __init__(
        self,
        task_func: Any,
        request_type: type[RequestType],
        response_type: type[ResponseType],
    ):
        self._task_func = task_func
        self._request_type = request_type
        self._response_type = response_type

    def run_in_process(self, request: RequestType) -> ResponseType:
        raw_response = self._task_func(request.dict())
        return self._response_type.parse_obj(raw_response)

    def run(
        self,
        request: RequestType,
        timeout: TimeoutType | None = None,
        celery_kwargs: dict[str, Any] | None = None,
    ) -> ResponseType:
        return self.run_async(request, celery_kwargs).get(timeout)

    def run_async(
        self, request: RequestType, celery_kwargs: dict[str, Any] | None = None
    ) -> AsyncResponse[ResponseType]:
        celery_kwargs = celery_kwargs or {}
        async_result = self._task_func.apply_async(
            args=(request.dict(),),
            **celery_kwargs,
        )
        return AsyncResponse[ResponseType](self._response_type, async_result)
