from datetime import datetime

from finbot.core import schema as core_schema
from finbot.core.schema import BaseModel


class NewHistoryEntryReport(BaseModel):
    history_entry_id: int
    valuation_date: datetime
    valuation_currency: str
    user_account_valuation: float
    valuation_change: core_schema.ValuationChange


class WriteHistoryResponse(BaseModel):
    report: NewHistoryEntryReport
