import datetime
from typing import cast

import aiohttp
from pydantic import BaseModel, AwareDatetime

from finbot.core.collections import drop_dict_items_with_null_values
from finbot.core.errors import FinbotError
from finbot.core.typing_extensions import JSON
from finbot.core.utils import some


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


class Transaction(BaseModel):
    transaction_id: str
    amount: float
    side: str
    operation_type: str
    currency: str
    local_currency: str
    label: str
    settled_at: AwareDatetime
    emitted_at: AwareDatetime
    updated_at: AwareDatetime
    status: str
    note: str | None
    reference: str | None
    initiator_id: str | None
    label_ids: list[str]
    category: str | None
    cashflow_category: dict[str, str | None] | None
    cashflow_subcategory: dict[str, str | None] | None
    id: str
    subject_type: str


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

    async def list_transactions(self, iban: str, created_at_from: datetime.datetime | None):
        all_transactions = []
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            total_pages = None
            page = 1
            while total_pages is None or page <= some(total_pages):
                async with session.get(
                    "https://thirdparty.qonto.com/v2/transactions",
                    headers={"Authorization": f"{self._creds[0]}:{self._creds[1]}"},
                    params=drop_dict_items_with_null_values({
                        "iban": iban,
                        "created_at_from": created_at_from.isoformat() if created_at_from else None,
                        "per_page": 100,
                        "page": page
                    })
                ) as resp:
                    payload = await self._handle_response(resp)
                    assert isinstance(payload, dict)
                    all_transactions.extend([Transaction.model_validate(txn) for txn in payload["transactions"]])
                    page += 1
                    if total_pages is None:
                        total_pages = payload["meta"]["total_pages"]
        return all_transactions
