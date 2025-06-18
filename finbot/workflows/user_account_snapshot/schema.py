from datetime import datetime, timedelta

from finbot.core.schema import ApplicationErrorData, BaseModel, CurrencyCode, LinkedAccountId
from finbot.providers.schema import ProviderId
from finbot.workflows.fetch_financial_data.schema import GetFinancialDataResponse, LineItem

DEFAULT_MAX_LINKED_ACCOUNT_SNAPSHOT_RETRIES = 3
DEFAULT_SNAPSHOT_TIMEOUT = timedelta(minutes=10)
DEFAULT_LINKED_ACCOUNT_SNAPSHOT_TIMEOUT = timedelta(seconds=300)


class SnapshotMetadata(BaseModel):
    id: int
    user_account_id: int
    requested_ccy: CurrencyCode


class SnapshotResultsCount(BaseModel):
    total: int
    failures: int


class SnapshotSummary(BaseModel):
    identifier: int
    start_time: datetime
    end_time: datetime
    results_count: SnapshotResultsCount


class TakeSnapshotRequest(BaseModel):
    user_account_id: int
    linked_account_ids: list[LinkedAccountId] | None
    timeout: timedelta = DEFAULT_SNAPSHOT_TIMEOUT


class TakeSnapshotResponse(BaseModel):
    snapshot: SnapshotSummary


class LinkedAccountSnapshotRequest(BaseModel):
    linked_account_id: LinkedAccountId
    provider_id: ProviderId
    encrypted_credentials: str
    line_items: list[LineItem]
    user_account_currency: CurrencyCode
    max_retries: int = DEFAULT_MAX_LINKED_ACCOUNT_SNAPSHOT_RETRIES
    timeout: timedelta = DEFAULT_LINKED_ACCOUNT_SNAPSHOT_TIMEOUT


class LinkedAccountSnapshotResponse(BaseModel):
    request: LinkedAccountSnapshotRequest
    snapshot_data: GetFinancialDataResponse | ApplicationErrorData


class TakeRawSnapshotRequest(BaseModel):
    user_account_id: int
    linked_account_ids: list[LinkedAccountId] | None


class TakeRawSnapshotResponse(BaseModel):
    entries: list[LinkedAccountSnapshotResponse]
