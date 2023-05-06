from datetime import datetime
from typing import Any, Literal

from pydantic import Extra, Field

from finbot.core.schema import BaseModel


class ErrorMetadata(BaseModel):
    user_message: str
    debug_message: str | None
    error_code: str | None
    exception_type: str | None
    trace: str | None

    class Config:
        extra = Extra.ignore


class AuthenticationPayload(BaseModel):
    access_token: str
    refresh_token: str


class UserAccount(BaseModel):
    id: int
    email: str
    full_name: str
    mobile_phone_number: str
    created_at: datetime
    updated_at: datetime | None


class Provider(BaseModel):
    id: str
    description: str
    website_url: str
    credentials_schema: Any
    created_at: datetime
    updated_at: datetime | None


class LinkedAccountStatusErrorEntry(BaseModel):
    scope: str
    error: ErrorMetadata


class LinkedAccountStatus(BaseModel):
    status: Literal["stable", "unstable"]
    errors: list[LinkedAccountStatusErrorEntry] | None
    last_snapshot_id: int
    last_snapshot_time: datetime


class LinkedAccount(BaseModel):
    id: int
    user_account_id: int
    account_name: str
    deleted: bool
    frozen: bool
    provider_id: str
    provider: Provider
    status: LinkedAccountStatus | None
    credentials: Any
    created_at: datetime
    updated_at: datetime | None


class SystemReport(BaseModel):
    finbot_version: str
    runtime: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    auth: AuthenticationPayload
    account: UserAccount


class HealthResponse(BaseModel):
    healthy: bool


class SystemReportResponse(BaseModel):
    system_report: SystemReport


class UpdateLinkedAccountMetadataRequest(BaseModel):
    account_name: str | None = None
    frozen: bool | None = None


class UpdateLinkedAccountMetadataResponse(BaseModel):
    pass


class LinkAccountCommitParams(BaseModel):
    do_validate: bool = Field(default=True, alias="validate")
    do_persist: bool = Field(default=True, alias="persist")


class LinkAccountRequest(BaseModel):
    provider_id: str
    credentials: Any
    account_name: str


class LinkAccountResponse(BaseModel):
    pass


class UpdateLinkedAccountCredentialsRequest(BaseModel):
    credentials: Any


class UpdateLinkedAccountCredentialsResponse(BaseModel):
    pass


class GetLinkedAccountsResponse(BaseModel):
    linked_accounts: list[LinkedAccount]


class GetLinkedAccountResponse(BaseModel):
    linked_account: LinkedAccount


class DeleteLinkedAccountResponse(BaseModel):
    pass
