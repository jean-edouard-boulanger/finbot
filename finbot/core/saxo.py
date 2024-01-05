from dataclasses import dataclass
from typing import Any, Literal

import requests

from finbot.core.pydantic_ import BaseModel


class DisplayAndFormat(BaseModel):
    Currency: str
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
    Currency: str
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
        self._session = requests.Session()
        self._api_key = api_key

    @property
    def reachable(self) -> bool:
        try:
            response = self._session.get(
                f"{self._settings.gateway_url}/status",
                timeout=1.0,
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def send_openapi_request(
        self,
        verb: Literal["GET"],
        resource: str,
        params: dict[str, str] | None = None,
    ) -> Any:
        resource = resource.lstrip("/")
        impl = getattr(self._session, verb.lower())
        response = impl(
            f"{self._settings.gateway_url}/openapi/{resource}",
            headers={"Authorization": f"Bearer {self._api_key}"},
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def openapi_get(
        self,
        resource: str,
        params: dict[str, str] | None = None,
    ) -> Any:
        return self.send_openapi_request(
            verb="GET",
            resource=resource,
            params=params,
        )

    def get_accounts(self) -> AccountsResponse:
        accounts_response_payload = self.openapi_get("port/v1/accounts/me")
        return AccountsResponse.parse_obj(accounts_response_payload)

    def get_account_positions(
        self,
        saxo_account: SaxoAccount,
    ) -> NetPositionsResponse:
        net_positions_payload = self.openapi_get(
            "port/v1/netpositions/",
            params={
                "AccountKey": saxo_account.AccountKey,
                "ClientKey": saxo_account.ClientKey,
                "FieldGroups": "SinglePositionBase,SinglePositionView,DisplayAndFormat,ExchangeInfo",
            },
        )
        return NetPositionsResponse.parse_obj(net_positions_payload)

    def get_account_balances(
        self,
        saxo_account: SaxoAccount,
    ) -> AccountBalancesResponse:
        account_balances_response_payload = self.openapi_get(
            "port/v1/balances/",
            params={
                "AccountKey": saxo_account.AccountKey,
                "ClientKey": saxo_account.ClientKey,
            },
        )
        return AccountBalancesResponse.parse_obj(account_balances_response_payload)
