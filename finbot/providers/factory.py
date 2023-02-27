from typing import TypeAlias

from finbot.providers import Base, Retired
from finbot.providers import (
    plaid_us,
    binance_us,
    credit_agricole_fr,
    aegon_targetplan_uk,
    kraken_us,
    qonto_us,
    google_sheets,
    dummy_uk,
)

ProviderId: TypeAlias = str


PROVIDERS: dict[ProviderId, type[Base]] = {
    "aegon_targetplan_uk": aegon_targetplan_uk.Api,
    "binance_us": binance_us.Api,
    "bittrex_us": Retired,
    "ca_fr": credit_agricole_fr.Api,
    "dummy_uk": dummy_uk.Api,
    "google_sheets": google_sheets.Api,
    "kraken_us": kraken_us.Api,
    "lending_works_uk": Retired,
    "october_fr": Retired,
    "plaid_us": plaid_us.Api,
    "qonto_us": qonto_us.Api,
    "vanguard_uk": Retired,
}


def get_provider(provider_id: str) -> type[Base]:
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        raise KeyError(f"unknown provider: {provider_id}")
    return provider
