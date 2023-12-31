import pytest

from finbot.core.crypto_market import cryptocurrency_code, is_cryptocurrency_code
from finbot.core.schema import CurrencyCode


@pytest.mark.parametrize(
    "symbol, expected",
    [
        ("ZBTC", True),
        ("ETH", False),
        ("EUR", False),
    ],
)
def test_is_cryptocurrency_code(
    symbol: str,
    expected: bool,
):
    assert is_cryptocurrency_code(symbol) is expected


@pytest.mark.parametrize(
    "symbol, expected",
    [
        ("BTC", "ZBTC"),
        ("ZETH", "ZETH"),
    ],
)
def test_cryptocurrency_code(
    symbol: str,
    expected: CurrencyCode,
):
    assert cryptocurrency_code(symbol) == expected
