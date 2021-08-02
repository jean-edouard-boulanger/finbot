from finbot.core import tracer
from finbot.clients.base import Base as ClientBase

from typing import Optional, Any
from enum import Enum


class LineItem(Enum):
    Balances = "balances"
    Assets = "assets"
    Liabilities = "liabilities"


class Error(RuntimeError):
    pass


class FinbotClient(ClientBase):
    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def get_financial_data(
        self,
        provider: str,
        credentials_data: dict[Any, Any],
        line_items: list[LineItem],
        account_metadata: Optional[str] = None,
        tracer_context: Optional[tracer.FlatContext] = None,
    ) -> dict:
        return self.post(
            "financial_data",
            payload=tracer.pack_context({
                "provider": provider,
                "credentials": credentials_data,
                "items": [item.value for item in line_items],
                "account_metadata": account_metadata
            }, tracer_context),
        )
