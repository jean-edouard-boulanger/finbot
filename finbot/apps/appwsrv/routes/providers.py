import logging

from fastapi import APIRouter

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.core import providers as appwsrv_providers
from finbot.apps.http_base import CurrentUserIdDep
from finbot.core.environment import get_plaid_environment
from finbot.core.errors import InvalidOperation, InvalidUserInput
from finbot.model import LinkedAccount, Provider, db, persist_scope, repository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/providers",
    tags=["Financial data providers"],
)


@router.put(
    "/",
    operation_id="update_or_create_financial_data_provider",
)
def update_or_create_provider(
    json: appwsrv_schema.CreateOrUpdateProviderRequest,
    _: CurrentUserIdDep,
) -> appwsrv_schema.CreateOrUpdateProviderResponse:
    """Update or create provider"""
    existing_provider = repository.find_provider(db.session, json.id)
    with persist_scope(existing_provider or Provider()) as provider:
        provider.id = json.id
        provider.description = json.description
        provider.website_url = json.website_url
        provider.credentials_schema = json.credentials_schema
    return appwsrv_schema.CreateOrUpdateProviderResponse(
        provider=serializer.serialize_provider(provider),
    )


@router.get(
    "/",
    operation_id="get_financial_data_providers",
)
def get_providers(
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetProvidersResponse:
    """Get providers"""
    return appwsrv_schema.GetProvidersResponse(
        providers=[
            serializer.serialize_provider(provider)
            for provider in db.session.query(Provider).all()
            if appwsrv_providers.is_provider_supported(provider)
        ]
    )


@router.get(
    "/{provider_id}/",
    operation_id="get_financial_data_provider",
)
def get_provider(
    provider_id: str,
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetProviderResponse:
    """Get provider"""
    provider = repository.find_provider(db.session, provider_id)
    if not provider:
        raise InvalidUserInput(f"Provider with id '${provider_id}' does not exist")
    return appwsrv_schema.GetProviderResponse(
        provider=serializer.serialize_provider(provider),
    )


@router.delete(
    "/{provider_id}/",
    operation_id="delete_financial_data_provider",
)
def delete_provider(
    provider_id: str,
    _: CurrentUserIdDep,
) -> appwsrv_schema.DeleteProviderResponse:
    """Delete provider"""
    provider = repository.get_provider(db.session, provider_id)
    linked_accounts: list[LinkedAccount] = provider.linked_accounts
    if len(linked_accounts) > 0:
        raise InvalidOperation("This provider is still in use")
    db.session.delete(provider)  # type: ignore
    db.session.commit()
    logging.info(f"deleted provider_id={provider_id}")
    return appwsrv_schema.DeleteProviderResponse()


@router.get(
    "/plaid/settings/",
    operation_id="get_plaid_settings",
)
def get_plaid_settings(
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetPlaidSettingsResponse:
    """Get plaid settings"""
    plaid_env = get_plaid_environment()
    if not plaid_env:
        return appwsrv_schema.GetPlaidSettingsResponse(settings=None)
    return appwsrv_schema.GetPlaidSettingsResponse(
        settings=appwsrv_schema.PlaidSettings(
            environment=plaid_env.environment,
            client_id=plaid_env.client_id,
            public_key=plaid_env.public_key,
        )
    )
