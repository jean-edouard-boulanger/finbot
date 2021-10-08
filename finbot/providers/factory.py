from typing import Any
from finbot.providers import (
    plaid_us,
    binance_us,
    credit_agricole_fr,
    vanguard_uk,
    october_fr,
    aegon_targetplan_uk,
    lending_works_uk,
    kraken_us,
    bittrex_us,
    qonto_us,
    google_sheets,
    dummy_uk,
)


class ProviderDescriptor(object):
    def __init__(self, description: str, api_module: Any) -> None:
        self.description = description
        self.api_module = api_module


PROVIDERS = {
    "plaid_us": ProviderDescriptor(description="Plaid (US)", api_module=plaid_us),
    "binance_us": ProviderDescriptor(description="Binance (US)", api_module=binance_us),
    "ca_fr": ProviderDescriptor(
        description="Credit agricole (FR)", api_module=credit_agricole_fr
    ),
    "vanguard_uk": ProviderDescriptor(
        description="Vanguard (UK)", api_module=vanguard_uk
    ),
    "october_fr": ProviderDescriptor(description="October (FR)", api_module=october_fr),
    "aegon_targetplan_uk": ProviderDescriptor(
        description="Aegon Target Plan (UK)", api_module=aegon_targetplan_uk
    ),
    "lending_works_uk": ProviderDescriptor(
        description="Lending Works (UK)", api_module=lending_works_uk
    ),
    "kraken_us": ProviderDescriptor(description="Kraken (US)", api_module=kraken_us),
    "bittrex_us": ProviderDescriptor(description="Bittrex (US)", api_module=bittrex_us),
    "google_sheets": ProviderDescriptor(
        description="Google Sheets", api_module=google_sheets
    ),
    "dummy_uk": ProviderDescriptor(
        description="Dummy (fake) provider", api_module=dummy_uk
    ),
    "qonto_us": ProviderDescriptor(description="Qonto (US)", api_module=qonto_us),
}


def get_provider(provider_id: str) -> ProviderDescriptor:
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        raise KeyError(f"unknown provider: {provider_id}")
    return provider
