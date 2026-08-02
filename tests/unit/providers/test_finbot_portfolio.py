from datetime import datetime, timezone
from typing import Any

import pytest

from finbot.core.schema import CurrencyCode
from finbot.core.securities_market import SecurityQuote, UnknownSecurity
from finbot.providers import finbot_portfolio
from finbot.providers.errors import UserConfigurationError
from finbot.providers.finbot_portfolio import (
    Api,
    Credentials,
    EntryData,
    PortfolioData,
    SectionData,
)
from finbot.providers.schema import AccountType, AssetClass, AssetType

PORTFOLIO_ID = 42
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def make_entry(**overrides: Any) -> EntryData:
    defaults: dict[str, Any] = {
        "id": 1,
        "is_liability": False,
        "name": "Riverside cottage",
        "asset_class": AssetClass.real_estate.value,
        "asset_type": AssetType.residential_property.value,
        "liability_type": None,
        "currency": CurrencyCode("EUR"),
        "units": 1.0,
        "is_proxy_priced": False,
        "manual_unit_price": 200_000.0,
        "proxy_symbol": None,
        "last_resolved_unit_price": None,
        "isin_code": None,
        "custom_values": None,
    }
    return EntryData(**{**defaults, **overrides})


def make_portfolio(*entries: EntryData) -> PortfolioData:
    return PortfolioData(
        portfolio_id=PORTFOLIO_ID,
        sections=(
            SectionData(
                section_id="properties",
                name="Properties",
                currency=CurrencyCode("EUR"),
                account_type=AccountType.other.value,
                account_sub_type=None,
                entries=entries,
            ),
        ),
    )


class FakeSecuritiesMarket:
    def __init__(self, quotes: dict[str, SecurityQuote]):
        self.quotes = quotes
        self.requested: list[str] = []

    async def async_get_quote_cached(self, symbol: str, with_name: bool = False) -> SecurityQuote:
        self.requested.append(symbol)
        if symbol not in self.quotes:
            raise UnknownSecurity(symbol)
        return self.quotes[symbol]


def make_provider(
    portfolio: PortfolioData,
    quotes: dict[str, SecurityQuote] | None = None,
) -> tuple[Api, FakeSecuritiesMarket]:
    market = FakeSecuritiesMarket(quotes or {})
    provider = Api(
        credentials=Credentials(portfolio_id=PORTFOLIO_ID),
        user_account_currency=CurrencyCode("GBP"),
        securities_market=market,  # type: ignore[arg-type]
    )
    provider._portfolio = portfolio
    return provider, market


@pytest.fixture(autouse=True)
def no_price_write_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prices are written back to the database, which unit tests do not have."""
    monkeypatch.setattr(finbot_portfolio, "_persist_resolved_prices", lambda prices: None)


GOLD_QUOTE = SecurityQuote(
    symbol="GC=F",
    name="Gold",
    currency=CurrencyCode("USD"),
    price=4000.0,
    as_of=NOW,
)


class TestGetAccounts:
    @pytest.mark.asyncio
    async def test_sections_are_mapped_to_sub_accounts(self):
        provider, _ = make_provider(make_portfolio(make_entry()))
        accounts = await provider.get_accounts()
        assert len(accounts) == 1
        assert accounts[0].id == "properties"
        assert accounts[0].name == "Properties"
        assert accounts[0].iso_currency == "EUR"
        assert accounts[0].type == AccountType.other
        assert accounts[0].sub_type is None


class TestGetAssets:
    @pytest.mark.asyncio
    async def test_manually_priced_entry(self):
        provider, _ = make_provider(make_portfolio(make_entry(units=2.0, manual_unit_price=1500.0)))
        assets = await provider.get_assets()
        item = assets.accounts[0].items[0]
        assert item.units == 2.0
        assert item.value_in_item_ccy == 3000.0
        assert item.value_in_account_ccy is None
        assert item.currency == "EUR"
        assert item.asset_class == AssetClass.real_estate
        assert item.asset_type == AssetType.residential_property

    @pytest.mark.asyncio
    async def test_proxy_priced_entry_uses_quote_price_and_currency(self):
        entry = make_entry(
            name="Gold",
            asset_class=AssetClass.commodities.value,
            asset_type=AssetType.precious_metal.value,
            units=12.5,
            is_proxy_priced=True,
            manual_unit_price=None,
            proxy_symbol="GC=F",
        )
        provider, market = make_provider(make_portfolio(entry), {"GC=F": GOLD_QUOTE})
        assets = await provider.get_assets()
        item = assets.accounts[0].items[0]
        assert item.value_in_item_ccy == 50_000.0
        assert item.currency == "USD"
        assert market.requested == ["GC=F"]

    @pytest.mark.asyncio
    async def test_custom_values_are_reported_as_provider_specific(self):
        entry = make_entry(custom_values={"City": "Bristol", "Ownership": "100%"})
        provider, _ = make_provider(make_portfolio(entry))
        assets = await provider.get_assets()
        assert assets.accounts[0].items[0].provider_specific == {
            "City": "Bristol",
            "Ownership": "100%",
        }

    @pytest.mark.asyncio
    async def test_liabilities_are_excluded_from_assets(self):
        provider, _ = make_provider(
            make_portfolio(
                make_entry(),
                make_entry(
                    id=2,
                    is_liability=True,
                    name="Mortgage",
                    asset_class=None,
                    asset_type=None,
                    liability_type="mortgage",
                    manual_unit_price=-150_000.0,
                ),
            )
        )
        assets = await provider.get_assets()
        assert [item.name for item in assets.accounts[0].items] == ["Riverside cottage"]

    @pytest.mark.asyncio
    async def test_missing_asset_classification_is_reported(self):
        provider, _ = make_provider(make_portfolio(make_entry(asset_class=None)))
        with pytest.raises(UserConfigurationError, match="asset class"):
            await provider.get_assets()

    @pytest.mark.asyncio
    async def test_missing_manual_price_is_reported(self):
        provider, _ = make_provider(make_portfolio(make_entry(manual_unit_price=None)))
        with pytest.raises(UserConfigurationError, match="no price set"):
            await provider.get_assets()


class TestProxyPriceFallback:
    @pytest.mark.asyncio
    async def test_falls_back_to_last_resolved_price(self):
        entry = make_entry(
            name="Gold",
            asset_class=AssetClass.commodities.value,
            asset_type=AssetType.precious_metal.value,
            units=10.0,
            is_proxy_priced=True,
            manual_unit_price=None,
            proxy_symbol="UNRESOLVABLE",
            last_resolved_unit_price=3500.0,
            currency=CurrencyCode("USD"),
        )
        provider, _ = make_provider(make_portfolio(entry))
        assets = await provider.get_assets()
        item = assets.accounts[0].items[0]
        assert item.value_in_item_ccy == 35_000.0
        assert item.currency == "USD"

    @pytest.mark.asyncio
    async def test_errors_when_there_is_nothing_to_fall_back_on(self):
        entry = make_entry(
            name="Gold",
            asset_class=AssetClass.commodities.value,
            asset_type=AssetType.precious_metal.value,
            is_proxy_priced=True,
            manual_unit_price=None,
            proxy_symbol="UNRESOLVABLE",
            last_resolved_unit_price=None,
        )
        provider, _ = make_provider(make_portfolio(entry))
        with pytest.raises(UserConfigurationError, match="could not be resolved"):
            await provider.get_assets()

    @pytest.mark.asyncio
    async def test_missing_proxy_symbol_is_reported(self):
        entry = make_entry(is_proxy_priced=True, manual_unit_price=None, proxy_symbol=None)
        provider, _ = make_provider(make_portfolio(entry))
        with pytest.raises(UserConfigurationError, match="no proxy symbol"):
            await provider.get_assets()


class TestGetLiabilities:
    @pytest.mark.asyncio
    async def test_liability_entry(self):
        entry = make_entry(
            id=2,
            is_liability=True,
            name="Mortgage",
            asset_class=None,
            asset_type=None,
            liability_type="mortgage",
            manual_unit_price=-150_000.0,
        )
        provider, _ = make_provider(make_portfolio(entry))
        liabilities = await provider.get_liabilities()
        item = liabilities.accounts[0].items[0]
        assert item.name == "Mortgage"
        assert item.type == "mortgage"
        assert item.value_in_item_ccy == -150_000.0
        assert item.currency == "EUR"

    @pytest.mark.asyncio
    async def test_assets_are_excluded_from_liabilities(self):
        provider, _ = make_provider(make_portfolio(make_entry()))
        liabilities = await provider.get_liabilities()
        assert liabilities.accounts[0].items == []


class TestPriceResolutionIsSharedAcrossLineItems:
    @pytest.mark.asyncio
    async def test_proxy_is_only_resolved_once_per_snapshot(self):
        entry = make_entry(
            name="Gold",
            asset_class=AssetClass.commodities.value,
            asset_type=AssetType.precious_metal.value,
            is_proxy_priced=True,
            manual_unit_price=None,
            proxy_symbol="GC=F",
        )
        provider, market = make_provider(make_portfolio(entry), {"GC=F": GOLD_QUOTE})
        await provider.get_assets()
        await provider.get_liabilities()
        assert market.requested == ["GC=F"]


class TestGetTransactions:
    @pytest.mark.asyncio
    async def test_transactions_are_not_supported(self):
        provider, _ = make_provider(make_portfolio(make_entry()))
        assert (await provider.get_transactions()).transactions == []
