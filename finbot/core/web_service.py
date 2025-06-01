from typing import Any, Optional, Self

import orjson
import requests
import requests.exceptions

from finbot.core import environment
from finbot.core import schema as core_schema
from finbot.core.errors import FinbotError
from finbot.core.serialization import serialize


class WebServiceClientError(FinbotError):
    pass


class WebServiceClient(object):
    service_name: str

    def __init__(self, server_endpoint: str):
        self._endpoint = server_endpoint

    def send_request(self, verb: str, route: str, payload: Optional[Any] = None) -> Any:
        resource = f"{self._endpoint}/{route}"
        if not hasattr(requests, verb.lower()):
            raise WebServiceClientError(f"unexpected verb: {verb} (while calling {resource})")
        dispatcher = getattr(requests, verb.lower())
        try:
            response = dispatcher(resource, json=serialize(payload))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise WebServiceClientError(f"error while sending request to {resource}: {e}")
        return orjson.loads(response.content)

    def get(self, route: str) -> Any:
        return self.send_request("get", route)

    def post(self, route: str, payload: Optional[Any] = None) -> Any:
        return self.send_request("post", route, payload)

    @property
    def healthy(self) -> bool:
        return core_schema.HealthResponse(**self.get("healthy/")).healthy

    @classmethod
    def create(cls) -> Self:
        return cls(environment.get_web_service_endpoint(cls.service_name))
