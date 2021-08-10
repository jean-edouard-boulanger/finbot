from finbot.core import tracer

from forex_python.converter import CurrencyRates

from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class Xccy(object):
    domestic: str
    foreign: str

    def __str__(self) -> str:
        return f"{self.domestic}{self.foreign}"

    def serialize(self) -> dict[str, str]:
        return {"domestic": self.domestic, "foreign": self.foreign}


def get_rates(pairs: set[Xccy]) -> dict[Xccy, float]:
    with tracer.sub_step("Query rate(s) from forex-python") as step:
        step.set_input(pairs)
        converter = CurrencyRates()
        rates = {
            pair: converter.get_rate(pair.domestic, pair.foreign) for pair in pairs
        }
        step.set_output(rates)
        return rates


def get_rate(pair: Xccy) -> float:
    return get_rates({pair})[pair]
