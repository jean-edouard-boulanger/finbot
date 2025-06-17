from datetime import datetime
from typing import Optional

from finbot.core import schema as core_schema
from finbot.core.schema import BaseModel


class ValuationRequest(BaseModel):
    user_account_id: int
    linked_accounts: Optional[list[int]] = None
    notify_valuation: bool = False


class ValuationResponse(BaseModel):
    history_entry_id: int
    user_account_valuation: float
    valuation_currency: str
    valuation_date: datetime
    valuation_change: core_schema.ValuationChange
