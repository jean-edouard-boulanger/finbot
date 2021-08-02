from finbot.core.utils import serialize

from typing import Optional, Any
from requests.exceptions import RequestException
import requests
import json


class Error(RuntimeError):
    pass


class Base(object):
    def __init__(self, server_endpoint: str):
        self._endpoint = server_endpoint

    def send_request(
        self, verb: str, route: str, payload: Optional[Any] = None
    ) -> dict:
        resource = f"{self._endpoint}/{route}"
        if not hasattr(requests, verb.lower()):
            raise Error(f"unexpected verb: {verb} (while calling {resource})")
        dispatcher = getattr(requests, verb.lower())
        try:
            response = dispatcher(resource, json=serialize(payload))
            response.raise_for_status()
        except RequestException as e:
            raise Error(f"error while sending request to {resource}: {e}")
        return json.loads(response.content)

    def get(self, route: str) -> dict[Any, Any]:
        return self.send_request("get", route)

    def post(self, route: str, payload: Optional[Any] = None) -> dict[Any, Any]:
        return self.send_request("post", route, payload)

    @property
    def healthy(self) -> bool:
        return self.get("healthy")["healthy"]
