import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated, Any, Literal

import aiohttp
from aiohttp import ClientPayloadError, ServerDisconnectedError
from pydantic import AwareDatetime, BaseModel, Discriminator, Tag

from finbot.core.collections import drop_dict_items_with_null_values
from finbot.core.schema import CurrencyCode
from finbot.core.utils import now_utc


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
    CreationDate: AwareDatetime


class AccountsResponse(BaseModel):
    Data: list[SaxoAccount]


class AccountBalancesResponse(BaseModel):
    CashAvailableForTrading: float
    TotalValue: float


class TransactionBooking(BaseModel):
    AmountType: str
    AmountTypeDisplay: str
    AmountTypeId: str
    BookedAmount: float
    BookingId: str
    ConversionCost: float
    ConversionRate: float
    CostClass: str
    CostSubClass: str
    Date: str
    ValueDate: str


class TransactionCashBalance(BaseModel):
    Available: float
    Balance: float
    Blocked: float


class TransactionCash(BaseModel):
    After: TransactionCashBalance
    Before: TransactionCashBalance


class TradeInstrument(BaseModel):
    AssetType: str
    Currency: CurrencyCode
    CurrencyDecimals: int
    Description: str
    ExchangeDescription: str
    ISINCode: str
    IssuerName: str
    PriceCurrency: str | None = None
    ResidualValue: float
    Symbol: str
    Uic: int


class CashInstrument(BaseModel):
    AssetType: str | None = None
    Currency: CurrencyCode | None = None
    CurrencyDecimals: int
    Description: str | None = None
    ExchangeDescription: str | None = None
    ISINCode: str | None = None
    IssuerName: str | None = None
    PriceCurrency: str | None = None
    ResidualValue: float | None = None
    Symbol: str
    Uic: int


class TransactionTrade(BaseModel):
    AdjustedTradeDate: str
    Direction: str
    ExchangeName: str
    IsSaxoCounterpart: bool
    OrderId: str
    PositionId: str
    Price: float
    SpreadCost: float
    StopLoss: float
    ToolId: str
    ToOpenOrClose: str
    ToOpenOrCloseDisplay: str
    TradeBarrierEventStatus: bool
    TradedQuantity: float
    TradedValue: float
    TradeEventType: str
    TradeEventTypeDisplay: str
    TradeExecutionTime: AwareDatetime
    TradeId: str
    TradeType: str
    Venue: str


class TransactionBase(BaseModel):
    AccountId: str
    BkRecordId: int
    BookedAmount: float
    BookingId: str | None = None
    Bookings: list[TransactionBooking]
    Cash: TransactionCash
    ConversionCost: float
    ConversionRate: float
    Currency: CurrencyCode
    CurrencyDecimals: int
    Date: str
    Event: str
    EventDisplay: str
    IsAdvisedTrade: bool
    IsIntradayData: bool
    IsReversal: bool
    OriginalTradeId: int
    TotalCost: float
    TransactionType: str
    TransactionTypeDisplay: str
    ValueDate: str


class TradeTransaction(TransactionBase):
    TransactionType: Literal["Trade"]
    FrontOfficeTradeId: str
    Instrument: TradeInstrument
    PositionId: str
    RealizedPnL: float | None = None
    RelatedPositionId: str
    RelatedTradeId: str
    TradeId: str
    Trades: list[TransactionTrade]
    Venue: str


class CashTransferTransaction(TransactionBase):
    TransactionType: Literal["CashTransfer"]
    FrontOfficeTradeId: str
    FundingSubType: str
    FundingSubTypeDisplay: str
    Instrument: CashInstrument
    PositionId: str
    RelatedPositionId: str
    RelatedTradeId: str
    UnderlyingInstrument: CashInstrument | None = None


class CashAmountTransaction(TransactionBase):
    TransactionType: Literal["CashAmount"]
    Instrument: CashInstrument
    UnderlyingInstrument: CashInstrument | None = None


Transaction = Annotated[
    Annotated[TradeTransaction, Tag("Trade")]
    | Annotated[CashTransferTransaction, Tag("CashTransfer")]
    | Annotated[CashAmountTransaction, Tag("CashAmount")],
    Discriminator("TransactionType"),
]


class AccountTransactionsResponse(BaseModel):
    Data: list[Transaction]


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
        _retries: int = 10,
        _retry_after: timedelta = timedelta(seconds=3.0),
    ) -> Any:
        resource = resource.lstrip("/")
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            impl = getattr(session, verb.lower())
            response: aiohttp.ClientResponse
            try:
                async with impl(
                    f"{self._settings.gateway_url}/openapi/{resource}",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    params=params,
                ) as response:
                    if not response.ok:
                        body = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"{response.reason}: {body}",
                            headers=response.headers,
                        )
                    return await response.json()
            except (ServerDisconnectedError, ClientPayloadError, aiohttp.ClientResponseError) as e:
                if isinstance(e, aiohttp.ClientResponseError) and "RateLimitExceeded" not in e.message:
                    raise
                logging.info(
                    f"openapi request failed ({type(e).__name__}),"
                    f" retrying in {_retry_after.total_seconds():.1f}s (retries left: {_retries - 1})"
                )
                if _retries > 0:
                    await asyncio.sleep(_retry_after.total_seconds())
                    return await self.send_openapi_request(
                        verb=verb,
                        resource=resource,
                        params=params,
                        _retries=_retries - 1,
                        _retry_after=timedelta(seconds=_retry_after.total_seconds() * 2.0),
                    )
                raise

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
        print(accounts_response_payload)
        return AccountsResponse.model_validate(accounts_response_payload)

    async def get_account_positions(
        self,
        saxo_account: SaxoAccount,
    ) -> NetPositionsResponse:
        payload = await self.openapi_get(
            "port/v1/netpositions/",
            params={
                "AccountKey": saxo_account.AccountKey,
                "ClientKey": saxo_account.ClientKey,
                "FieldGroups": "SinglePositionBase,SinglePositionView,DisplayAndFormat,ExchangeInfo",
            },
        )
        return NetPositionsResponse.model_validate(payload)

    async def get_account_balances(
        self,
        saxo_account: SaxoAccount,
    ) -> AccountBalancesResponse:
        payload = await self.openapi_get(
            "port/v1/balances/",
            params={
                "AccountKey": saxo_account.AccountKey,
                "ClientKey": saxo_account.ClientKey,
            },
        )
        return AccountBalancesResponse.model_validate(payload)

    async def get_account_transactions(
        self,
        saxo_account: SaxoAccount,
        from_date: AwareDatetime | None = None,
    ) -> AccountTransactionsResponse:
        current_from_date = max(from_date or saxo_account.CreationDate, saxo_account.CreationDate).date()
        all_transactions = []
        chunk_time_window = timedelta(days=90)
        while current_from_date <= now_utc().date():
            end_date = current_from_date + chunk_time_window
            payload = await self.openapi_get(
                "hist/v1/transactions",
                params=drop_dict_items_with_null_values(
                    {
                        "AccountKeys": saxo_account.AccountKey,
                        "ClientKey": saxo_account.ClientKey,
                        "FromDate": current_from_date.isoformat(),
                        "ToDate": end_date.isoformat(),
                    }
                ),
            )
            new_transactions = AccountTransactionsResponse.model_validate(payload).Data
            all_transactions.extend(new_transactions)
            current_from_date = end_date + timedelta(days=1)
        return AccountTransactionsResponse(Data=all_transactions)
