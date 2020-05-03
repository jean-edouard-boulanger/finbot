from finbot.core import tracer
from typing import Dict, Optional
import requests
import json


class Error(RuntimeError):
    pass


class HistoryClient(object):
    def __init__(self, server_endpoint: str):
        self.server_endpoint = server_endpoint

    def write_history(self,
                      snapshot_id: str,
                      tracer_context: Optional[tracer.FlatContext] = None) -> Dict:
        payload = {tracer.CONTEXT_TAG: tracer_context.serialize()} if tracer_context else None
        response = requests.post(f"{self.server_endpoint}/history/{snapshot_id}/write", json=payload)
        if not response:
            raise Error(f"failure while writing history (code {response.status_code})")
        return json.loads(response.content)
