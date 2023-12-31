from functools import cache

from pycoingecko import CoinGeckoAPI

from finbot.core.errors import FinbotError
from finbot.core.schema import CurrencyCode

CRYPTOCURRENCY_CODE_PREFIX = "Z"


class Error(FinbotError):
    pass


class CryptoMarket(object):
    def __init__(self, impl: CoinGeckoAPI | None = None):
        self._api = impl or CoinGeckoAPI()
        self._symbols_to_id: dict[str, str] = {entry["symbol"]: entry["id"] for entry in self._api.get_coins_list()}

    def _get_coin_id(self, symbol: str) -> str:
        return self._symbols_to_id[symbol.lower()]

    @cache
    def get_spot_cached(self, source_crypto_ccy: str, target_ccy: str) -> float:
        return self.get_spot(source_crypto_ccy, target_ccy)

    def get_spot(self, source_crypto_ccy: str, target_ccy: str) -> float:
        target_ccy = target_ccy.lower()
        coin_id = self._get_coin_id(source_crypto_ccy)
        result = self._api.get_price(coin_id, target_ccy)
        if coin_id not in result:
            raise Error(f"no spot for {source_crypto_ccy} ({coin_id})")
        return float(result[coin_id][target_ccy])


def is_cryptocurrency_code(symbol: str | None) -> bool:
    """Checks whether a symbol is a cryptocurrency code (i.e. currency code prefixed with `Z`)
    Examples:
        - ZBTC: True
        - EUR: False
    """
    return symbol is not None and len(symbol) > 3 and symbol.startswith(CRYPTOCURRENCY_CODE_PREFIX)


def cryptocurrency_code(symbol: str) -> CurrencyCode:
    """Converts an arbitrary symbol to a cryptocurrency code (i.e. BTC -> ZBTC)"""
    symbol = symbol.upper()
    if is_cryptocurrency_code(symbol):
        return CurrencyCode(symbol)
    return CurrencyCode(f"{CRYPTOCURRENCY_CODE_PREFIX}{symbol.upper()}")
