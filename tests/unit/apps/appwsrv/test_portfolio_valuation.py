from decimal import Decimal
from typing import Any

import pytest

from finbot.apps.appwsrv.core import portfolio_valuation
from finbot.apps.appwsrv.core.portfolio_valuation import estimate_portfolio_values
from finbot.core import fx_market
from finbot.core.schema import CurrencyCode
from finbot.model import PortfolioEntryPriceSource

GBP = CurrencyCode("GBP")


class FakeEntry:
    def __init__(
        self,
        entry_id: int,
        currency: str,
        units: float,
        *,
        manual: float | None = None,
        last_resolved: float | None = None,
    ):
        self.id = entry_id
        self.currency = currency
        self.units = Decimal(str(units))
        self.price_source = PortfolioEntryPriceSource.Manual if manual is not None else PortfolioEntryPriceSource.Proxy
        self.manual_unit_price = Decimal(str(manual)) if manual is not None else None
        self.last_resolved_unit_price = Decimal(str(last_resolved)) if last_resolved is not None else None


class FakeSection:
    def __init__(self, section_id: int, entries: list[FakeEntry], currency: str = "GBP"):
        self.id = section_id
        self.entries = entries
        self.currency = currency


class FakePortfolio:
    def __init__(self, portfolio_id: int, sections: list[FakeSection]):
        self.id = portfolio_id
        self.sections = sections


def patch_rates(monkeypatch: pytest.MonkeyPatch, rates: dict[tuple[str, str], float | None]) -> list[int]:
    """Stub the FX layer, recording how many times it is consulted."""
    calls: list[int] = []

    async def fake_get_rates(pairs: set[fx_market.Xccy]) -> dict[fx_market.Xccy, float | None]:
        calls.append(len(pairs))
        return {pair: rates.get((pair.domestic, pair.foreign)) for pair in pairs}

    monkeypatch.setattr(fx_market, "async_get_rates", fake_get_rates)
    return calls


def portfolio(*entries: FakeEntry, section_currency: str = "GBP") -> Any:
    return FakePortfolio(1, [FakeSection(10, list(entries), section_currency)])


class TestEstimatePortfolioValues:
    @pytest.mark.asyncio
    async def test_values_manual_holdings_in_their_own_currency(self, monkeypatch: pytest.MonkeyPatch):
        patch_rates(monkeypatch, {})
        estimates = await estimate_portfolio_values([portfolio(FakeEntry(1, "GBP", 2, manual=1000.0))], GBP)
        assert estimates[1].total == 2000.0
        assert estimates[1].by_entry[1] == 2000.0
        assert estimates[1].by_section[10] == 2000.0
        assert estimates[1].currency == "GBP"

    @pytest.mark.asyncio
    async def test_converts_foreign_currency_holdings(self, monkeypatch: pytest.MonkeyPatch):
        patch_rates(monkeypatch, {("USD", "GBP"): 0.8})
        estimates = await estimate_portfolio_values([portfolio(FakeEntry(1, "USD", 1, manual=500.0))], GBP)
        assert estimates[1].total == 400.0

    @pytest.mark.asyncio
    async def test_uses_the_last_price_read_for_tracked_holdings(self, monkeypatch: pytest.MonkeyPatch):
        """Stale is fine: the estimate must never wait on the market."""
        patch_rates(monkeypatch, {})
        estimates = await estimate_portfolio_values([portfolio(FakeEntry(1, "GBP", 10, last_resolved=25.0))], GBP)
        assert estimates[1].total == 250.0

    @pytest.mark.asyncio
    async def test_skips_holdings_that_have_never_been_priced(self, monkeypatch: pytest.MonkeyPatch):
        patch_rates(monkeypatch, {})
        estimates = await estimate_portfolio_values(
            [portfolio(FakeEntry(1, "GBP", 1, manual=100.0), FakeEntry(2, "GBP", 1))], GBP
        )
        assert estimates[1].total == 100.0
        assert 2 not in estimates[1].by_entry

    @pytest.mark.asyncio
    async def test_skips_holdings_whose_rate_is_unavailable(self, monkeypatch: pytest.MonkeyPatch):
        patch_rates(monkeypatch, {("USD", "GBP"): None})
        estimates = await estimate_portfolio_values(
            [portfolio(FakeEntry(1, "GBP", 1, manual=100.0), FakeEntry(2, "USD", 1, manual=999.0))], GBP
        )
        assert estimates[1].total == 100.0
        assert 2 not in estimates[1].by_entry

    @pytest.mark.asyncio
    async def test_totals_a_section_in_its_own_reporting_currency(self, monkeypatch: pytest.MonkeyPatch):
        """A section reports in its currency; the portfolio rolls up into the account's."""
        patch_rates(monkeypatch, {("USD", "EUR"): 0.9, ("USD", "GBP"): 0.8})
        estimates = await estimate_portfolio_values(
            [portfolio(FakeEntry(1, "USD", 1, manual=100.0), section_currency="EUR")], GBP
        )
        assert estimates[1].by_section[10] == 90.0, "section total is in EUR"
        assert estimates[1].total == 80.0, "portfolio total is in GBP"

    @pytest.mark.asyncio
    async def test_section_total_needs_no_conversion_when_currencies_match(self, monkeypatch: pytest.MonkeyPatch):
        patch_rates(monkeypatch, {("EUR", "GBP"): 0.85})
        estimates = await estimate_portfolio_values(
            [portfolio(FakeEntry(1, "EUR", 2, manual=50.0), section_currency="EUR")], GBP
        )
        assert estimates[1].by_section[10] == 100.0
        assert estimates[1].total == 85.0

    @pytest.mark.asyncio
    async def test_asks_for_every_rate_at_once(self, monkeypatch: pytest.MonkeyPatch):
        calls = patch_rates(monkeypatch, {("USD", "GBP"): 0.8, ("EUR", "GBP"): 0.85})
        portfolios = [
            FakePortfolio(1, [FakeSection(10, [FakeEntry(1, "USD", 1, manual=100.0)])]),
            FakePortfolio(2, [FakeSection(20, [FakeEntry(2, "EUR", 1, manual=100.0)])]),
        ]
        estimates = await estimate_portfolio_values(portfolios, GBP)  # type: ignore[arg-type]
        assert calls == [2], "rates should be resolved in a single round trip"
        assert estimates[1].total == 80.0
        assert estimates[2].total == 85.0

    @pytest.mark.asyncio
    async def test_reports_nothing_when_rates_cannot_be_resolved(self, monkeypatch: pytest.MonkeyPatch):
        """Callers fall back to the last snapshot rather than showing a number that is wrong."""

        async def boom(pairs: set[fx_market.Xccy]) -> dict[fx_market.Xccy, float | None]:
            raise RuntimeError("fx is down")

        monkeypatch.setattr(fx_market, "async_get_rates", boom)
        estimates = await estimate_portfolio_values([portfolio(FakeEntry(1, "USD", 1, manual=100.0))], GBP)
        assert estimates == {}

    @pytest.mark.asyncio
    async def test_does_not_call_fx_when_everything_is_already_in_the_target_currency(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        calls = patch_rates(monkeypatch, {})
        await estimate_portfolio_values([portfolio(FakeEntry(1, "GBP", 1, manual=100.0))], GBP)
        assert calls == []


class TestUnitPrice:
    def test_prefers_the_manual_price_when_the_user_sets_it(self):
        entry = FakeEntry(1, "GBP", 1, manual=10.0)
        entry.last_resolved_unit_price = Decimal("99")
        assert portfolio_valuation._unit_price(entry) == 10.0  # type: ignore[arg-type]

    def test_falls_back_to_the_last_resolved_price_for_tracked_holdings(self):
        entry = FakeEntry(1, "GBP", 1, last_resolved=42.0)
        assert portfolio_valuation._unit_price(entry) == 42.0  # type: ignore[arg-type]

    def test_is_none_when_there_is_no_price_at_all(self):
        assert portfolio_valuation._unit_price(FakeEntry(1, "GBP", 1)) is None  # type: ignore[arg-type]
