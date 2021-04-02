from typing import Dict, Optional, List
import requests
import json

from finbot.core import tracer


class Error(RuntimeError):
    pass


class SnapClient(object):
    def __init__(self, server_endpoint: str):
        self.server_endpoint = server_endpoint

    def take_snapshot(
        self,
        account_id: int,
        linked_accounts: Optional[List[int]] = None,
        tracer_context: Optional[tracer.FlatContext] = None,
    ) -> Dict:
        payload = {
            tracer.CONTEXT_TAG: tracer_context.serialize() if tracer_context else None,
            "linked_accounts": linked_accounts,
        }
        response = requests.post(
            f"{self.server_endpoint}/snapshot/{account_id}/take", json=payload
        )
        if not response:
            raise Error(f"failure while taking snapshot (code {response.status_code})")
        return json.loads(response.content)
