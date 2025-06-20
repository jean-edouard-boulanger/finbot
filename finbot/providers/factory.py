from typing import TypeAlias

from finbot.providers import (
    aegon_targetplan_uk,
    binance_us,
    credit_agricole_fr,
    dummy_uk,
    google_sheets,
    kraken_us,
    plaid_us,
    qonto_us,
    saxo_gw_fr,
    suravenir_fr,
)
from finbot.providers.base import ProviderBase, RetiredProvider
from finbot.providers.errors import UnknownProvider
from finbot.providers.interactive_brokers_uk import provider as interactive_brokers_uk

ProviderId: TypeAlias = str


PROVIDERS: dict[ProviderId, type[ProviderBase]] = {
    "aegon_targetplan_uk": aegon_targetplan_uk.Api,
    "binance_us": binance_us.Api,
    "bittrex_us": RetiredProvider,
    "ca_fr": credit_agricole_fr.Api,
    "dummy_uk": dummy_uk.Api,
    "google_sheets": google_sheets.Api,
    "interactive_brokers_uk": interactive_brokers_uk.Api,
    "kraken_us": kraken_us.Api,
    "lending_works_uk": RetiredProvider,
    "october_fr": RetiredProvider,
    "plaid_us": plaid_us.Api,
    "qonto_us": qonto_us.Api,
    "saxo_gw_fr": saxo_gw_fr.Api,
    "suravenir_fr": suravenir_fr.Api,
    "vanguard_uk": RetiredProvider,
}


def get_provider(provider_id: ProviderId) -> type[ProviderBase]:
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        raise UnknownProvider(provider_id)
    return provider
