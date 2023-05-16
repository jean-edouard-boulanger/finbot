from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TakeSnapshotRequest(BaseModel):
    linked_account_ids: Optional[list[int]] = None


class SnapshotResultsCount(BaseModel):
    total: int
    failures: int


class SnapshotSummary(BaseModel):
    identifier: int
    start_time: datetime
    end_time: datetime
    results_count: SnapshotResultsCount


class TakeSnapshotResponse(BaseModel):
    snapshot: SnapshotSummary
