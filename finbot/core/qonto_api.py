from typing import cast

import requests
from pydantic import BaseModel

from finbot.core.errors import FinbotError
from finbot.core.typing_extensions import JSON


class BankAccount(BaseModel):
    slug: str
    iban: str
    bic: str
    currency: str
    balance: float
    balance_cents: str
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
        super().__init__("not authorized to access this Qonto account data")


class QontoApi(object):
    def __init__(self, identifier: str, secret_key: str):
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"{identifier}:{secret_key}"})

    @staticmethod
    def _handle_response(response: requests.Response) -> JSON:
        response.raise_for_status()
        payload = response.json()
        if "errors" in payload:
            errors = payload["errors"]
            if len(errors) == 1 and errors[0]["code"] == "unauthorized":
                raise Unauthorized()
            raise QontoError(
                "Errors: " + ", ".join(error["detail"] for error in errors)
            )
        return cast(JSON, payload)

    def list_organizations(self) -> list[Organization]:
        response = self._session.get("https://thirdparty.qonto.com/v2/organization")
        payload = QontoApi._handle_response(response)
        assert isinstance(payload, dict)
        return [Organization.parse_obj(payload["organization"])]
