from typing import cast

import aiohttp
from pydantic import BaseModel

from finbot.core.errors import FinbotError
from finbot.core.typing_extensions import JSON


class BankAccount(BaseModel):
    slug: str
    iban: str
    bic: str
    currency: str
    balance: float
    balance_cents: float
    authorized_balance: float
    authorized_balance_cents: int
    name: str
    updated_at: str
    status: str
    main: bool


class Organization(BaseModel):
    slug: str
    legal_name: str
    bank_accounts: list[BankAccount]


class QontoError(FinbotError):
    def __init__(self, error_message: str) -> None:
        super().__init__(error_message)


class Unauthorized(QontoError):
    def __init__(self) -> None:
        super().__init__("not authorized to access this Qonto account")


class QontoApi(object):
    def __init__(self, identifier: str, secret_key: str):
        self._creds = (identifier, secret_key)

    @staticmethod
    async def _handle_response(response: aiohttp.ClientResponse) -> JSON:
        payload = await response.json()
        if "errors" in payload:
            errors = payload["errors"]
            if len(errors) == 1 and errors[0]["code"] == "unauthorized":
                raise Unauthorized()
            raise QontoError("Errors: " + ", ".join(error["detail"] for error in errors))
        return cast(JSON, payload)

    async def list_organizations(self) -> list[Organization]:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(
                "https://thirdparty.qonto.com/v2/organization",
                headers={"Authorization": f"{self._creds[0]}:{self._creds[1]}"},
            ) as resp:
                payload = await self._handle_response(resp)
                assert isinstance(payload, dict)
                return [Organization.model_validate(payload["organization"])]
