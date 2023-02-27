from datetime import timedelta
from typing import Generic, Optional, Type, TypeVar, Union

from celery.result import AsyncResult
from pydantic import BaseModel

from finbot.apps.workersrv import workersrv
from finbot.apps.workersrv.schema import ValuationRequest, ValuationResponse

ResponseType = TypeVar("ResponseType", bound=BaseModel)


TimeoutType = Union[int, float, timedelta]


def _get_timeout(timeout: Optional[TimeoutType]) -> Optional[float]:
    if timeout is None:
        return None
    if isinstance(timeout, (int, float)):
        return float(timeout)
    return timeout.total_seconds()


class AsyncResponse(Generic[ResponseType]):
    def __init__(self, response_type: Type[ResponseType], async_result: AsyncResult):
        self._response_type = response_type
        self._async_result = async_result

    def get(self, timeout: Optional[TimeoutType] = None) -> ResponseType:
        return self._response_type.parse_obj(
            self._async_result.get(timeout=_get_timeout(timeout))
        )


class WorkerClient(object):
    def get_valuation_async(
        self, request: ValuationRequest
    ) -> AsyncResponse[ValuationResponse]:
        async_result = workersrv.handle_valuation_request.delay(request.dict())
        return AsyncResponse(ValuationResponse, async_result)

    def trigger_valuation(self, request: ValuationRequest) -> None:
        self.get_valuation_async(request)

    def get_valuation(
        self, request: ValuationRequest, timeout: Optional[TimeoutType] = None
    ) -> ValuationResponse:
        return self.get_valuation_async(request).get(timeout=timeout)

    def get_healthy(self, timeout: Optional[TimeoutType] = None) -> bool:
        healthy: bool = workersrv.handle_healthy.delay().get(
            timeout=_get_timeout(timeout)
        )
        return healthy
