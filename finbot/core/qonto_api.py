from finbot.core.errors import FinbotError

from typing import Any, Protocol
from dataclasses import dataclass
import requests


@dataclass
class BankAccount:
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

    @staticmethod
    def deserialize(data: dict[str, Any]) -> "BankAccount":
        return BankAccount(**data)


@dataclass
class Organization:
    slug: str
    legal_name: str
    bank_accounts: list[BankAccount]

    @staticmethod
    def deserialize(data: dict[str, Any]) -> "Organization":
        return Organization(
            slug=data["slug"],
            legal_name=data["legal_name"],
            bank_accounts=[
                BankAccount.deserialize(entry) for entry in data["bank_accounts"]
            ],
        )


class AuthenticationMethod(Protocol):
    def as_http_header(self) -> dict[str, str]:
        ...


class SimpleAuthentication(AuthenticationMethod):
    def __init__(self, identifier: str, secret_key: str):
        self.identifier = identifier
        self.secret_key = secret_key

    def as_http_header(self) -> dict[str, str]:
        return {"Authorization": f"{self.identifier}:{self.secret_key}"}


class QontoError(FinbotError):
    def __init__(self, error_message: str) -> None:
        super().__init__(error_message)


class Unauthorized(QontoError):
    def __init__(self) -> None:
        super().__init__("not authorized to access this Qonto account data")


class QontoApi(object):
    def __init__(self, auth_method: AuthenticationMethod):
        self._session = requests.Session()
        self._session.headers.update(auth_method.as_http_header())

    @staticmethod
    def _handle_response(response: requests.Response) -> Any:
        response.raise_for_status()
        payload = response.json()
        if "errors" in payload:
            errors = payload["errors"]
            if len(errors) == 1 and errors[0]["code"] == "unauthorized":
                raise Unauthorized()
            raise QontoError(
                "Errors: " + ", ".join(error["detail"] for error in errors)
            )
        return payload

    def list_organizations(self) -> list[Organization]:
        response = self._session.get("https://thirdparty.qonto.com/v2/organization")
        payload = QontoApi._handle_response(response)
        return [Organization.deserialize(payload["organization"])]
