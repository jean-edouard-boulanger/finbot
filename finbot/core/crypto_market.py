from finbot.core.errors import FinbotError
from finbot.core import tracer

from functools import lru_cache
from pycoingecko import CoinGeckoAPI


class Error(FinbotError):
    pass


class CoinGeckoWrapper(object):
    def __init__(self, coingecko_api: CoinGeckoAPI):
        self._api = coingecko_api
        self._symbols_to_id = {
            entry["symbol"]: entry["id"] for entry in self._api.get_coins_list()
        }

    @lru_cache(None)
    def get_spot_cached(self, source_crypto_ccy: str, target_ccy: str) -> float:
        return self.get_spot(source_crypto_ccy, target_ccy)

    def get_spot(self, source_crypto_ccy: str, target_ccy: str) -> float:
        target_ccy = target_ccy.lower()
        coin_id = self._symbols_to_id[source_crypto_ccy.lower()]
        pair_str = f"{source_crypto_ccy}/{target_ccy}"
        with tracer.sub_step(f"Query {pair_str} rate from CoinGecko") as step:
            step.set_input(f"{coin_id}/{target_ccy}")
            result = self._api.get_price(coin_id, target_ccy)
            step.set_output(result)
            if coin_id not in result:
                raise Error(f"no spot for {coin_id}")
        return float(result[coin_id][target_ccy])
