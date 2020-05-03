from finbot.core import tracer
from typing import Dict, Optional
import requests
import json


class Error(RuntimeError):
    pass


class SnapClient(object):
    def __init__(self, server_endpoint: str):
        self.server_endpoint = server_endpoint

    def take_snapshot(self,
                      account_id: int,
                      tracer_context: Optional[tracer.FlatContext] = None) -> Dict:
        payload = {tracer.CONTEXT_TAG: tracer_context.serialize()} if tracer_context else None
        response = requests.post(f"{self.server_endpoint}/snapshot/{account_id}/take", json=payload)
        if not response:
            raise Error(f"failure while taking snapshot (code {response.status_code})")
        return json.loads(response.content)
