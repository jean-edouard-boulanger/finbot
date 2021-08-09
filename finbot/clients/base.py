from finbot.core.errors import FinbotError
from finbot.core.serialization import serialize

from typing import Optional, Any
import requests.exceptions
import requests
import json


class ClientError(FinbotError):
    pass


class Base(object):
    def __init__(self, server_endpoint: str):
        self._endpoint = server_endpoint

    def send_request(
        self, verb: str, route: str, payload: Optional[Any] = None
    ) -> dict:
        resource = f"{self._endpoint}/{route}"
        if not hasattr(requests, verb.lower()):
            raise ClientError(f"unexpected verb: {verb} (while calling {resource})")
        dispatcher = getattr(requests, verb.lower())
        try:
            response = dispatcher(resource, json=serialize(payload))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ClientError(f"error while sending request to {resource}: {e}")
        return json.loads(response.content)

    def get(self, route: str) -> dict[Any, Any]:
        return self.send_request("get", route)

    def post(self, route: str, payload: Optional[Any] = None) -> dict[Any, Any]:
        return self.send_request("post", route, payload)

    @property
    def healthy(self) -> bool:
        return self.get("healthy")["healthy"]
