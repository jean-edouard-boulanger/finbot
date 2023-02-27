from enum import Enum
from typing import Any, Optional

from finbot.clients.base import Base as ClientBase


class LineItem(Enum):
    Balances = "balances"
    Assets = "assets"
    Liabilities = "liabilities"


class FinbotClient(ClientBase):
    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def get_financial_data(
        self,
        provider: str,
        credentials_data: dict[str, Any],
        line_items: list[LineItem],
        account_metadata: Optional[str] = None,
    ) -> Any:
        return self.post(
            "financial_data",
            {
                "provider": provider,
                "credentials": credentials_data,
                "items": [item.value for item in line_items],
                "account_metadata": account_metadata,
            },
        )
