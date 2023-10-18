from datetime import datetime

from finbot.core.schema import BaseModel


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
