import logging
from datetime import datetime, timezone
from typing import Any, Generator

from pydantic import AwareDatetime, SecretStr

from finbot.core import saxo
from finbot.core.environment import get_saxo_gateway_url
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.utils import some
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError, UnsupportedFinancialInstrument
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    AssetClass,
    Assets,
    AssetsEntry,
    AssetType,
    Transaction,
    Transactions,
    TransactionType,
)


class Credentials(BaseModel):
    api_key: SecretStr


class Api(ProviderBase):
    description = "Saxo OpenAPI Gateway (FR)"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        saxo_gateway_url = get_saxo_gateway_url()
        assert saxo_gateway_url, "Saxo provider is not properly configured"
        self._client = saxo.SaxoGatewayClient(
            settings=saxo.SaxoGatewaySettings(gateway_url=saxo_gateway_url),
            api_key=credentials.api_key.get_secret_value(),
        )
        self._accounts: list[saxo.SaxoAccount] | None = None

    async def initialize(self) -> None:
        try:
            self._accounts = (await self._client.get_accounts()).Data
        except Exception as e:
            raise AuthenticationError(str(e))

    async def get_accounts(self) -> list[Account]:
        return [account for (account, _) in self._iter_accounts()]

    async def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=account.id,
                    items=(await self._get_account_assets(saxo_account=saxo_account)),
                )
                for (account, saxo_account) in self._iter_accounts()
            ]
        )

    async def get_transactions(self, from_date: AwareDatetime | None = None) -> Transactions:
        all_transactions: list[Transaction] = []
        for account, saxo_account in self._iter_accounts():
            response = await self._client.get_account_transactions(saxo_account, from_date)
            for t in response.Data:
                all_transactions.append(_make_saxo_transaction(t, account.id))
        return Transactions(transactions=all_transactions)

    async def _get_account_assets(self, saxo_account: saxo.SaxoAccount) -> list[Asset]:
        assets: list[Asset] = []
        if cash_available := (await self._client.get_account_balances(saxo_account)).CashAvailableForTrading:
            currency = CurrencyCode(saxo_account.Currency)
            assets.append(
                Asset.cash(
                    currency=currency,
                    is_domestic=currency == self.user_account_currency,
                    amount=cash_available,
                )
            )
        for position in (await self._client.get_account_positions(saxo_account)).Data:
            assets.append(_make_asset(position))
        return assets

    def _iter_accounts(self) -> Generator[tuple[Account, saxo.SaxoAccount], None, None]:
        for raw_account_data in some(self._accounts):
            yield (
                Account(
                    id=raw_account_data.AccountKey,
                    name=raw_account_data.DisplayName,
                    iso_currency=CurrencyCode(raw_account_data.Currency),
                    type=AccountType.investment,
                    sub_type="brokerage",
                ),
                raw_account_data,
            )


def _make_asset(
    position: saxo.NetPosition,
) -> Asset:
    asset_type = position.SinglePosition.PositionBase.AssetType
    if asset_type.lower() in ("etf", "etn", "etc"):
        return Asset(
            name=position.DisplayAndFormat.Description,
            type="equity",
            asset_class=(AssetClass.commodities if asset_type.lower() == "etc" else AssetClass.equities),
            asset_type=AssetType[asset_type.upper()],
            value_in_item_ccy=position.SinglePosition.PositionView.MarketValue,
            units=position.SinglePosition.PositionBase.Amount,
            currency=position.DisplayAndFormat.Currency,
            provider_specific={
                "Asset currency": position.DisplayAndFormat.Currency,
                "Symbol": position.DisplayAndFormat.Symbol,
                "Description": position.DisplayAndFormat.Description,
                "Listing exchange": position.Exchange.Description,
                "Current price": position.SinglePosition.PositionView.CurrentPrice,
                "P&L": position.SinglePosition.PositionView.ProfitLossOnTrade,
            },
        )
    raise UnsupportedFinancialInstrument(asset_type, position.DisplayAndFormat.Symbol)


_CASH_AMOUNT_EVENT_MAP: dict[str, TransactionType] = {
    "Client Interest": TransactionType.interest_earned,
    "Cancel Client Interest": TransactionType.adjustment,
    "Exchange Subscription Fee": TransactionType.fee,
    "Corporate Actions - Advanced Income Tax": TransactionType.tax,
    "Corporate Actions - Social Tax": TransactionType.tax,
    "Advanced Income Tax": TransactionType.tax,
    "Social Tax": TransactionType.tax,
}

logger = logging.getLogger(__name__)


def _parse_saxo_date(date_str: str) -> AwareDatetime:
    return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)


def _make_saxo_trade_transaction(t: saxo.TradeTransaction, account_id: str) -> Transaction:
    event = t.Event
    if event == "Buy":
        txn_type = TransactionType.buy
    elif event == "Sell":
        txn_type = TransactionType.sell
    else:
        txn_type = TransactionType.other

    trade = t.Trades[0]
    fee = sum(abs(b.BookedAmount) for b in t.Bookings if b.AmountType == "Commission")

    return Transaction(
        transaction_id=str(t.BkRecordId),
        account_id=account_id,
        transaction_date=_parse_saxo_date(t.Date),
        effective_date=_parse_saxo_date(t.ValueDate),
        transaction_type=txn_type,
        amount=t.BookedAmount,
        currency=t.Currency,
        description=f"{event.upper()} {abs(trade.TradedQuantity)} {t.Instrument.Symbol} @ {trade.Price}",
        symbol=t.Instrument.Symbol,
        units=abs(trade.TradedQuantity),
        unit_price=trade.Price,
        fee=fee if fee else None,
        provider_specific={
            "ISIN": t.Instrument.ISINCode,
            "Exchange": t.Instrument.ExchangeDescription,
            "RealizedPnL": t.RealizedPnL,
        },
    )


def _make_saxo_cash_transfer_transaction(t: saxo.CashTransferTransaction, account_id: str) -> Transaction:
    event = t.Event
    sub_type = t.FundingSubType

    if event == "Deposit":
        if sub_type == "IntraClientTransfer":
            txn_type = TransactionType.transfer_in
        else:
            txn_type = TransactionType.deposit
    elif event == "Withdrawal":
        if sub_type == "IntraClientTransfer":
            txn_type = TransactionType.transfer_out
        else:
            txn_type = TransactionType.withdrawal
    else:
        txn_type = TransactionType.other

    return Transaction(
        transaction_id=str(t.BkRecordId),
        account_id=account_id,
        transaction_date=_parse_saxo_date(t.Date),
        effective_date=_parse_saxo_date(t.ValueDate),
        transaction_type=txn_type,
        amount=t.BookedAmount,
        currency=t.Currency,
        description=f"{t.EventDisplay} - {t.FundingSubTypeDisplay}",
    )


def _make_saxo_cash_amount_transaction(t: saxo.CashAmountTransaction, account_id: str) -> Transaction:
    txn_type = _CASH_AMOUNT_EVENT_MAP.get(t.Event)
    if txn_type is None:
        logger.warning(f"Unknown CashAmount event: {t.Event!r}, mapping to 'other'")
        txn_type = TransactionType.other

    return Transaction(
        transaction_id=str(t.BkRecordId),
        account_id=account_id,
        transaction_date=_parse_saxo_date(t.Date),
        effective_date=_parse_saxo_date(t.ValueDate),
        transaction_type=txn_type,
        amount=t.BookedAmount,
        currency=t.Currency,
        description=t.EventDisplay,
    )


def _make_saxo_transaction(t: saxo.Transaction, account_id: str) -> Transaction:
    if isinstance(t, saxo.TradeTransaction):
        return _make_saxo_trade_transaction(t, account_id)
    elif isinstance(t, saxo.CashTransferTransaction):
        return _make_saxo_cash_transfer_transaction(t, account_id)
    elif isinstance(t, saxo.CashAmountTransaction):
        return _make_saxo_cash_amount_transaction(t, account_id)
    else:
        raise ValueError(f"Unknown Saxo transaction type: {type(t)}")
