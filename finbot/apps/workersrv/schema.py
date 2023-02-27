from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ValuationRequest(BaseModel):
    user_account_id: int
    linked_accounts: Optional[list[int]] = None


class ValuationChange(BaseModel):
    change_1hour: float
    change_1day: float
    change_1week: float
    change_1month: float
    change_6months: float
    change_1year: float
    change_2years: float


class ValuationResponse(BaseModel):
    history_entry_id: int
    user_account_valuation: float
    valuation_currency: str
    valuation_date: datetime
    valuation_change: ValuationChange
