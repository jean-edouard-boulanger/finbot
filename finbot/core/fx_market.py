from dataclasses import dataclass
from typing import Optional

import quickforex

from finbot.core.errors import FinbotError


@dataclass(frozen=True, eq=True)
class Xccy(object):
    domestic: str
    foreign: str

    def __str__(self) -> str:
        return f"{self.domestic}{self.foreign}"

    def serialize(self) -> dict[str, str]:
        return {"domestic": self.domestic, "foreign": self.foreign}

    def to_quickforex(self) -> quickforex.CurrencyPair:
        return quickforex.CurrencyPair(self.domestic, self.foreign)


def _xccy_to_quickforex(xccy: Xccy) -> quickforex.CurrencyPair:
    return quickforex.CurrencyPair(xccy.domestic, xccy.foreign)


def _xccy_from_quickforex(xccy: quickforex.CurrencyPair) -> Xccy:
    return Xccy(xccy.domestic, xccy.foreign)


def _format_quickforex_xccy(xccy: quickforex.CurrencyPair) -> str:
    return f"{xccy.domestic}/{xccy.foreign}"


class Error(FinbotError):
    pass


def get_rates(pairs: set[Xccy]) -> dict[Xccy, Optional[float]]:
    rates: dict[Xccy, Optional[float]] = {
        pair: 1.0 for pair in pairs if pair.foreign == pair.domestic
    }
    pairs_needing_lookup: set[quickforex.CurrencyPair] = {
        _xccy_to_quickforex(pair) for pair in pairs if pair not in rates
    }
    if pairs_needing_lookup:
        pairs_str = ",".join(
            _format_quickforex_xccy(pair) for pair in pairs_needing_lookup
        )
        try:
            quickforex_rates = quickforex.get_latest_rates(pairs_needing_lookup)
        except Exception as e:
            raise Error(
                f"Error while getting rates for currency pairs {pairs_str}: {e}"
            ) from e
        for currency_pair, rate in quickforex_rates.items():
            rates[_xccy_from_quickforex(currency_pair)] = float(rate)
    for pair in pairs:
        if pair not in rates:
            rates[pair] = None
    return rates


def get_rate(pair: Xccy) -> Optional[float]:
    return get_rates({pair}).get(pair)
