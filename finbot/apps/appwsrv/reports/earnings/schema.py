from datetime import datetime

from finbot.core.schema import BaseModel


class AggregationDescription(BaseModel):
    as_str: str


class Metrics(BaseModel):
    first_date: datetime
    first_value: float
    last_date: datetime
    last_value: float
    min_value: float
    max_value: float
    abs_change: float
    rel_change: float


class ReportEntry(BaseModel):
    aggregation: AggregationDescription
    metrics: Metrics


class EarningsReport(BaseModel):
    currency: str
    entries: list[ReportEntry]
    rollup: Metrics
