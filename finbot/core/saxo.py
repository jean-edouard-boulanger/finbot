from dataclasses import dataclass
from typing import Any, Literal

import aiohttp
from pydantic import BaseModel

from finbot.core.schema import CurrencyCode


class DisplayAndFormat(BaseModel):
    Currency: CurrencyCode
    Description: str
    Symbol: str


class Exchange(BaseModel):
    Description: str
    ExchangeId: str


class SinglePositionBase(BaseModel):
    AccountId: str
    AccountKey: str
    Amount: float
    AssetType: str


class SinglePositionView(BaseModel):
    CurrentPrice: float
    MarketValue: float
    ProfitLossOnTrade: float


class SinglePosition(BaseModel):
    PositionBase: SinglePositionBase
    PositionId: str
    PositionView: SinglePositionView


class NetPosition(BaseModel):
    DisplayAndFormat: DisplayAndFormat
    Exchange: Exchange
    NetPositionId: str
    SinglePosition: SinglePosition


class NetPositionsResponse(BaseModel):
    Data: list[NetPosition]


class SaxoAccount(BaseModel):
    AccountKey: str
    ClientKey: str
    Currency: CurrencyCode
    DisplayName: str


class AccountsResponse(BaseModel):
    Data: list[SaxoAccount]


class AccountBalancesResponse(BaseModel):
    CashAvailableForTrading: float
    TotalValue: float


@dataclass(frozen=True)
class SaxoGatewaySettings:
    gateway_url: str


class SaxoGatewayClient:
    def __init__(self, settings: SaxoGatewaySettings, api_key: str | None):
        self._settings = settings
        self._api_key = api_key

    async def send_openapi_request(
        self,
        verb: Literal["GET"],
        resource: str,
        params: dict[str, str] | None = None,
    ) -> Any:
        resource = resource.lstrip("/")
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            impl = getattr(session, verb.lower())
            response: aiohttp.ClientResponse
            async with impl(
                f"{self._settings.gateway_url}/openapi/{resource}",
                headers={"Authorization": f"Bearer {self._api_key}"},
                params=params,
            ) as response:
                return await response.json()

    async def openapi_get(
        self,
        resource: str,
        params: dict[str, str] | None = None,
    ) -> Any:
        return await self.send_openapi_request(
            verb="GET",
            resource=resource,
            params=params,
        )

    async def get_accounts(self) -> AccountsResponse:
        accounts_response_payload = await self.openapi_get("port/v1/accounts/me")
        return AccountsResponse.model_validate(accounts_response_payload)

    async def get_account_positions(
        self,
        saxo_account: SaxoAccount,
    ) -> NetPositionsResponse:
        net_positions_payload = await self.openapi_get(
            "port/v1/netpositions/",
            params={
                "AccountKey": saxo_account.AccountKey,
                "ClientKey": saxo_account.ClientKey,
                "FieldGroups": "SinglePositionBase,SinglePositionView,DisplayAndFormat,ExchangeInfo",
            },
        )
        return NetPositionsResponse.model_validate(net_positions_payload)

    async def get_account_balances(
        self,
        saxo_account: SaxoAccount,
    ) -> AccountBalancesResponse:
        account_balances_response_payload = await self.openapi_get(
            "port/v1/balances/",
            params={
                "AccountKey": saxo_account.AccountKey,
                "ClientKey": saxo_account.ClientKey,
            },
        )
        return AccountBalancesResponse.model_validate(account_balances_response_payload)
