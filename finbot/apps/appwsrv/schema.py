from datetime import datetime

from finbot.core.schema import BaseModel


class AuthenticationPayload(BaseModel):
    access_token: str
    refresh_token: str


class UserAccount(BaseModel):
    id: int
    email: str
    full_name: str
    mobile_phone_number: str
    created_at: datetime
    updated_at: datetime


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
