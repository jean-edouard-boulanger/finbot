from dataclasses import dataclass
from typing import Any, Literal

import requests


@dataclass(frozen=True)
class SaxoGatewaySettings:
    gateway_url: str


class SaxoGatewayClient:
    def __init__(self, settings: SaxoGatewaySettings, api_key: str | None):
        self._settings = settings
        self._session = requests.Session()
        self._api_key = api_key

    @property
    def reachable(self) -> bool:
        try:
            response = self._session.get(
                f"{self._settings.gateway_url}/status", timeout=1.0
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def send_openapi_request(self, verb: Literal["GET"], resource: str) -> Any:
        resource = resource.lstrip("/")
        impl = getattr(self._session, verb.lower())
        response = impl(
            f"{self._settings.gateway_url}/openapi/{resource}",
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        return response.json()

    def openapi_get(self, resource: str) -> Any:
        return self.send_openapi_request("GET", resource)
