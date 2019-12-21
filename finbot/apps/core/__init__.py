from finbot.providers import (
    credit_agricole_fr, 
    vanguard_uk,
    october_fr,
    aegon_targetplan_uk,
    lending_works_uk,
    barclays_uk
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
    "ca_fr": Provider(
        description="Credit agricole",
        api_module=credit_agricole_fr
    ),
    "vanguard_uk": Provider(
        description="Vanguard (UK)",
        api_module=vanguard_uk
    ),
    "october_fr": Provider(
        description="October",
        api_module=october_fr
    ),
    "aegon_targetplan_uk": Provider(
        description="Aegon Target Plan",
        api_module=aegon_targetplan_uk
    ),
    "lending_works_uk": Provider(
        description="Lending Works",
        api_module=lending_works_uk
    ),
    "barclays_uk": Provider(
        description="Barclays",
        api_module=barclays_uk
    )
}
