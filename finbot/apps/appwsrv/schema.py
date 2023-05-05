from datetime import datetime

from pydantic import BaseModel


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


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    auth: AuthenticationPayload
    account: UserAccount
