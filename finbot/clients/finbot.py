from finbot.core import tracer
from typing import Dict, List, Optional
from enum import Enum
import json
import requests


def json_dumps(data):
    return json.dumps(data, indent=4)


class LineItem(Enum):
    Balances = "balances"
    Assets = "assets"
    Liabilities = "liabilities"


class Error(RuntimeError):
    pass


class FinbotClient(object):
    def __init__(self, server_endpoint: str):
        self.server_endpoint = server_endpoint

    def get_providers(self) -> Dict:
        endpoint = f"{self.server_endpoint}/providers"
        return json.loads(requests.get(endpoint).content)

    def get_financial_data(self,
                           provider: str,
                           credentials_data: Dict,
                           line_items: List[LineItem],
                           tracer_context: Optional[tracer.FlatContext] = None) -> Dict:
        endpoint = f"{self.server_endpoint}/financial_data"
        response = requests.post(endpoint, json={
            "provider": provider,
            "credentials": credentials_data,
            "items": [item.value for item in line_items],
            tracer.CONTEXT_TAG: tracer_context.serialize() if tracer_context else None
        })
        if not response:
            raise Error(f"failure while getting financial data (code {response.status_code})")
        return json.loads(response.content)
