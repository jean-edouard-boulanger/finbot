from finbot.providers import (
    plaid_us,
    amex_us,
    binance_us,
    hl_uk,
    credit_agricole_fr,
    vanguard_uk,
    october_fr,
    aegon_targetplan_uk,
    lending_works_uk,
    barclays_uk,
    barclaycard_uk,
    kraken_us,
    bittrex_us,
    google_sheets,
    dummy_uk
)


class Provider(object):
    def __init__(self, description, api_module):
        self.description = description
        self.api_module = api_module


def get_provider(provider_id):
    provider = get_provider.providers.get(provider_id)
    if provider is None:
        raise KeyError(f"unknown provider: {provider_id}") 
    return provider


get_provider.providers = {
    "plaid_us": Provider(
        description="Plaid (US)",
        api_module=plaid_us
    ),
    "amex_us": Provider(
        description="American express (US)",
        api_module=amex_us
    ),
    "binance_us": Provider(
        description="Binance (US)",
        api_module=binance_us
    ),
    "ca_fr": Provider(
        description="Credit agricole (FR)",
        api_module=credit_agricole_fr
    ),
    "hl_uk": Provider(
        description="Hargreaves Lansdown (UK)",
        api_module=hl_uk
    ),
    "vanguard_uk": Provider(
        description="Vanguard (UK)",
        api_module=vanguard_uk
    ),
    "october_fr": Provider(
        description="October (FR)",
        api_module=october_fr
    ),
    "aegon_targetplan_uk": Provider(
        description="Aegon Target Plan (UK)",
        api_module=aegon_targetplan_uk
    ),
    "lending_works_uk": Provider(
        description="Lending Works (UK)",
        api_module=lending_works_uk
    ),
    "barclays_uk": Provider(
        description="Barclays (UK)",
        api_module=barclays_uk
    ),
    "barclaycard_uk": Provider(
        description="Barclaydcard (UK)",
        api_module=barclaycard_uk
    ),
    "kraken_us": Provider(
        description="Kraken (US)",
        api_module=kraken_us
    ),
    "bittrex_us": Provider(
        description="Bittrex (US)",
        api_module=bittrex_us
    ),
    "google_sheets": Provider(
        description="Google Sheets",
        api_module=google_sheets
    ),
    "dummy_uk": Provider(
        description="Dummy (fake) provider",
        api_module=dummy_uk
    )
}
