from finbot.core.utils import serialize

from typing import Optional, Any
import requests
import json


class Base(object):
    def __init__(self, server_endpoint: str):
        self._endpoint = server_endpoint

    def send_request(
        self, verb: str, route: str, payload: Optional[Any] = None
    ) -> dict:
        dispatcher = getattr(requests, verb.lower())
        resource = f"{self._endpoint}/{route}"
        response = dispatcher(resource, json=serialize(payload))
        response.raise_for_status()
        return json.loads(response.content)

    def get(self, route: str) -> dict:
        return self.send_request("get", route)

    def post(self, route: str, payload: Optional[Any] = None) -> dict:
        return self.send_request("post", route, payload)

    @property
    def healthy(self) -> bool:
        return self.get("healthy")["healthy"]