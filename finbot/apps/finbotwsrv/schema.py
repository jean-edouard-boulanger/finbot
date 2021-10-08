from typing import Optional, Any, Literal

from pydantic import BaseModel


LineItemLiteral = Literal["balances", "assets", "liabilities"]


class FinancialDataRequest(BaseModel):
    provider: str
    credentials: Any
    items: list[LineItemLiteral]
    account_metadata: Optional[str] = None
