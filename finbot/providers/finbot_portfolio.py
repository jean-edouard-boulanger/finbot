"""Provider backing Finbot-managed portfolios.

Unlike every other provider, this one has no external counterparty: the portfolio contents are
maintained by the user through the Finbot application itself, and read straight from the database.
Entries are valued as `units x unit price`, where the unit price is either typed in by the user
(a house, re-valued every couple of years) or resolved from Yahoo Finance through a proxy security
(gold, a tracker fund, ...).
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from finbot.core.async_ import aexec
from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.securities_market import SecuritiesMarket
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError, UserConfigurationError
from finbot.providers.schema import (
    Account,
    AccountType,
    Asset,
    AssetClass,
    Assets,
    AssetsEntry,
    AssetType,
    Liabilities,
    LiabilitiesEntry,
    Liability,
    ProviderSpecificPayloadType,
)

logger = logging.getLogger(__name__)


class Credentials(BaseModel):
    portfolio_id: int


@dataclass(frozen=True)
class EntryData:
    id: int
    is_liability: bool
    name: str
    asset_class: str | None
    asset_type: str | None
    liability_type: str | None
    currency: CurrencyCode
    units: float
    is_proxy_priced: bool
    manual_unit_price: float | None
    proxy_symbol: str | None
    last_resolved_unit_price: float | None
    isin_code: str | None
    custom_values: ProviderSpecificPayloadType | None


@dataclass(frozen=True)
class SectionData:
    section_id: str
    name: str
    currency: CurrencyCode
    account_type: str
    account_sub_type: str | None
    entries: tuple[EntryData, ...]


@dataclass(frozen=True)
class PortfolioData:
    portfolio_id: int
    sections: tuple[SectionData, ...]


@dataclass(frozen=True)
class ResolvedPrice:
    entry_id: int
    unit_price: float
    currency: CurrencyCode
    resolved_at: datetime | None
    """When the price was freshly resolved from the market, `None` when falling back to the last known price."""


def _load_portfolio(portfolio_id: int) -> PortfolioData:
    from finbot import model

    with model.ScopedSession() as session:
        portfolio = session.query(model.Portfolio).filter_by(id=portfolio_id).one_or_none()
        if portfolio is None:
            raise AuthenticationError(f"Portfolio {portfolio_id} does not exist (it may have been deleted)")
        return PortfolioData(
            portfolio_id=portfolio_id,
            sections=tuple(
                SectionData(
                    section_id=section.section_id,
                    name=section.name,
                    currency=CurrencyCode(section.currency),
                    account_type=section.account_type,
                    account_sub_type=section.account_sub_type,
                    entries=tuple(
                        EntryData(
                            id=entry.id,
                            is_liability=entry.item_type == model.SubAccountItemType.Liability,
                            name=entry.name,
                            asset_class=entry.asset_class,
                            asset_type=entry.asset_type,
                            liability_type=entry.liability_type,
                            currency=CurrencyCode(entry.currency),
                            units=float(entry.units),
                            is_proxy_priced=entry.price_source == model.PortfolioEntryPriceSource.Proxy,
                            manual_unit_price=(
                                float(entry.manual_unit_price) if entry.manual_unit_price is not None else None
                            ),
                            proxy_symbol=entry.proxy_symbol,
                            last_resolved_unit_price=(
                                float(entry.last_resolved_unit_price)
                                if entry.last_resolved_unit_price is not None
                                else None
                            ),
                            isin_code=entry.isin_code,
                            custom_values=entry.custom_values or None,
                        )
                        for entry in section.entries
                    ),
                )
                for section in portfolio.sections
            ),
        )


def _persist_resolved_prices(prices: list[ResolvedPrice]) -> None:
    from finbot import model

    fresh_prices = [price for price in prices if price.resolved_at is not None]
    if not fresh_prices:
        return
    with model.ScopedSession() as session:
        for price in fresh_prices:
            entry = session.query(model.PortfolioEntry).filter_by(id=price.entry_id).one_or_none()
            if entry is None:
                continue
            entry.last_resolved_unit_price = Decimal(str(price.unit_price))
            entry.last_resolved_price_at = price.resolved_at
            entry.currency = price.currency
        session.commit()


class Api(ProviderBase):
    description = "Finbot managed portfolio"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        securities_market: SecuritiesMarket | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._portfolio_id = credentials.portfolio_id
        self._securities_market = securities_market or SecuritiesMarket()
        self._portfolio: PortfolioData | None = None
        self._prices: dict[int, ResolvedPrice] | None = None

    async def initialize(self) -> None:
        # Deliberately does not resolve any market price: this is also the credentials validation path.
        self._portfolio = await aexec(_load_portfolio, self._portfolio_id)

    @property
    def portfolio(self) -> PortfolioData:
        if self._portfolio is None:
            raise AuthenticationError("Portfolio was not initialized")
        return self._portfolio

    async def get_accounts(self) -> list[Account]:
        return [
            Account(
                id=section.section_id,
                name=section.name,
                iso_currency=section.currency,
                type=AccountType(section.account_type),
                sub_type=section.account_sub_type,
            )
            for section in self.portfolio.sections
        ]

    async def get_assets(self) -> Assets:
        prices = await self._resolve_prices()
        return Assets(
            accounts=[
                AssetsEntry(
                    account_id=section.section_id,
                    items=[
                        self._make_asset(entry, prices[entry.id]) for entry in section.entries if not entry.is_liability
                    ],
                )
                for section in self.portfolio.sections
            ]
        )

    async def get_liabilities(self) -> Liabilities:
        prices = await self._resolve_prices()
        return Liabilities(
            accounts=[
                LiabilitiesEntry(
                    account_id=section.section_id,
                    items=[
                        self._make_liability(entry, prices[entry.id]) for entry in section.entries if entry.is_liability
                    ],
                )
                for section in self.portfolio.sections
            ]
        )

    async def _resolve_prices(self) -> dict[int, ResolvedPrice]:
        """Price every entry once per snapshot (both the assets and liabilities line items need them)."""
        if self._prices is None:
            prices = [
                await self._resolve_entry_price(entry)
                for section in self.portfolio.sections
                for entry in section.entries
            ]
            await aexec(_persist_resolved_prices, prices)
            self._prices = {price.entry_id: price for price in prices}
        return self._prices

    async def _resolve_entry_price(self, entry: EntryData) -> ResolvedPrice:
        if not entry.is_proxy_priced:
            if entry.manual_unit_price is None:
                raise UserConfigurationError(f"Entry '{entry.name}' has no price set")
            return ResolvedPrice(
                entry_id=entry.id,
                unit_price=entry.manual_unit_price,
                currency=entry.currency,
                resolved_at=None,
            )
        symbol = entry.proxy_symbol
        if not symbol:
            raise UserConfigurationError(f"Entry '{entry.name}' is proxy-priced but has no proxy symbol set")
        try:
            quote = await self._securities_market.async_get_quote_cached(symbol)
            return ResolvedPrice(
                entry_id=entry.id,
                unit_price=quote.price,
                currency=quote.currency,
                resolved_at=quote.as_of,
            )
        except Exception:
            logger.warning(
                f"could not resolve proxy security '{symbol}' for entry '{entry.name}', "
                f"falling back to the last known price",
                exc_info=True,
            )
            if entry.last_resolved_unit_price is None:
                raise UserConfigurationError(
                    f"Entry '{entry.name}' is priced against proxy security '{symbol}', which could not be"
                    f" resolved, and has no previously resolved price to fall back on."
                )
            return ResolvedPrice(
                entry_id=entry.id,
                unit_price=entry.last_resolved_unit_price,
                currency=entry.currency,
                resolved_at=None,
            )

    @staticmethod
    def _make_asset(entry: EntryData, price: ResolvedPrice) -> Asset:
        if not entry.asset_class or not entry.asset_type:
            raise UserConfigurationError(f"Entry '{entry.name}' is missing its asset class or asset type")
        asset_class = AssetClass(entry.asset_class)
        asset_type = AssetType(entry.asset_type)
        return Asset(
            name=entry.name,
            type=f"{asset_class.value} {asset_type.value}",
            asset_class=asset_class,
            asset_type=asset_type,
            value_in_item_ccy=entry.units * price.unit_price,
            units=entry.units,
            currency=price.currency,
            isin_code=entry.isin_code,
            provider_specific=entry.custom_values,
        )

    @staticmethod
    def _make_liability(entry: EntryData, price: ResolvedPrice) -> Liability:
        return Liability(
            name=entry.name,
            type=entry.liability_type or "other",
            value_in_item_ccy=entry.units * price.unit_price,
            currency=price.currency,
            provider_specific=entry.custom_values,
        )
