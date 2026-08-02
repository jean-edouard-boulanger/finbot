"""Fast, approximate valuation of portfolios for the editing screens.

The authoritative number comes from the snapshot pipeline, which reads every proxy security and
records the rates it used. That takes long enough to be unusable while someone is typing, so this
values a portfolio from what is already stored: the prices the user set, the last price read for
each tracked holding, and cached FX rates.

It is therefore an estimate, and is labelled as one wherever it is shown.
"""

import logging
from dataclasses import dataclass, field

from finbot.core import fx_market
from finbot.core.schema import CurrencyCode
from finbot.model import Portfolio, PortfolioEntry, PortfolioEntryPriceSource

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PortfolioValuationEstimate:
    currency: str
    total: float
    by_section: dict[int, float] = field(default_factory=dict)
    by_entry: dict[int, float] = field(default_factory=dict)


def _unit_price(entry: PortfolioEntry) -> float | None:
    """The most recent price known for this holding, without going to the market for it."""
    raw = (
        entry.manual_unit_price
        if entry.price_source == PortfolioEntryPriceSource.Manual
        else entry.last_resolved_unit_price
    )
    return float(raw) if raw is not None else None


async def estimate_portfolio_values(
    portfolios: list[Portfolio],
    valuation_ccy: CurrencyCode,
) -> dict[int, PortfolioValuationEstimate]:
    """Value every provided portfolio, in one round trip to the rates.

    Sections are totalled in their own reporting currency and the portfolio in the user's, which
    is how the snapshot pipeline stacks them up: a holding is worth something in its own currency,
    the sub-account reports in its, and the account rolls everything into one.

    Returns nothing for a portfolio whose rates could not be resolved: callers fall back to the
    last snapshot rather than showing a number that is quietly wrong.
    """
    pairs: set[fx_market.Xccy] = set()
    for portfolio in portfolios:
        for section in portfolio.sections:
            for entry in section.entries:
                for target in (valuation_ccy, section.currency):
                    if entry.currency != target:
                        pairs.add(fx_market.Xccy(entry.currency, target))
    try:
        rates = await fx_market.async_get_rates(pairs) if pairs else {}
    except Exception:
        logger.warning("could not resolve rates to estimate portfolio values", exc_info=True)
        return {}

    def convert(amount: float, currency: str, target: str) -> float | None:
        if currency == target:
            return amount
        rate = rates.get(fx_market.Xccy(currency, target))
        return amount * rate if rate is not None else None

    estimates: dict[int, PortfolioValuationEstimate] = {}
    for portfolio in portfolios:
        by_entry: dict[int, float] = {}
        by_section: dict[int, float] = {}
        total = 0.0
        for section in portfolio.sections:
            section_total = 0.0
            for entry in section.entries:
                unit_price = _unit_price(entry)
                if unit_price is None:
                    continue
                amount = float(entry.units) * unit_price
                in_section_ccy = convert(amount, entry.currency, section.currency)
                if in_section_ccy is not None:
                    section_total += in_section_ccy
                in_valuation_ccy = convert(amount, entry.currency, valuation_ccy)
                if in_valuation_ccy is not None:
                    by_entry[entry.id] = in_valuation_ccy
                    total += in_valuation_ccy
            by_section[section.id] = section_total
        estimates[portfolio.id] = PortfolioValuationEstimate(
            currency=valuation_ccy,
            total=total,
            by_section=by_section,
            by_entry=by_entry,
        )
    return estimates
