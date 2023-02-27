from typing import Any, Literal

from pydantic import BaseModel


LineItemLiteral = Literal["balances", "assets", "liabilities"]


class FinancialDataRequest(BaseModel):
    provider: str
    credentials: dict[str, Any]
    items: list[LineItemLiteral]
    account_metadata: str | None = None
