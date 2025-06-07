from cachetools import TTLCache, cached
from pycoingecko import CoinGeckoAPI

from finbot.core.async_ import aexec
from finbot.core.errors import FinbotError


class Error(FinbotError):
    pass


class CryptoMarket(object):
    def __init__(self, impl: CoinGeckoAPI | None = None):
        self._api = impl or CoinGeckoAPI()
        self._symbols_to_id: dict[str, str] = {entry["symbol"]: entry["id"] for entry in self._api.get_coins_list()}

    def _get_coin_id(self, symbol: str) -> str:
        return self._symbols_to_id[symbol.lower()]

    @cached(TTLCache(maxsize=10_000, ttl=3600))
    def get_spot_cached(self, source_crypto_ccy: str, target_ccy: str) -> float:
        return self.get_spot(source_crypto_ccy, target_ccy)

    def get_spot(self, source_crypto_ccy: str, target_ccy: str) -> float:
        target_ccy = target_ccy.lower()
        coin_id = self._get_coin_id(source_crypto_ccy)
        result = self._api.get_price(coin_id, target_ccy)
        if coin_id not in result:
            raise Error(f"no spot for {source_crypto_ccy} ({coin_id})")
        return float(result[coin_id][target_ccy])

    async def async_get_spot_cached(self, source_crypto_ccy: str, target_ccy: str) -> float:
        return await aexec(self.get_spot_cached, source_crypto_ccy, target_ccy)

    async def async_get_spot(self, source_crypto_ccy: str, target_ccy: str) -> float:
        return await aexec(self.get_spot, source_crypto_ccy, target_ccy)
