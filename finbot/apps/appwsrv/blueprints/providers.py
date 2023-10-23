import logging

from flask import Blueprint

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.core import providers as appwsrv_providers
from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.spec import spec
from finbot.core.environment import get_plaid_environment
from finbot.core.errors import InvalidOperation, InvalidUserInput
from finbot.core.spec_tree import JWT_REQUIRED, ResponseSpec
from finbot.core.web_service import jwt_required, service_endpoint
from finbot.model import LinkedAccount, Provider, repository

logger = logging.getLogger(__name__)

providers_api = Blueprint(
    name="providers_api", import_name=__name__, url_prefix=f"{API_URL_PREFIX}/providers"
)

ENDPOINTS_TAGS = ["Financial data providers"]


@providers_api.route("/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.CreateOrUpdateProviderResponse,
    ),
    operation_id="update_or_create_financial_data_provider",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def update_or_create_provider(
    json: appwsrv_schema.CreateOrUpdateProviderRequest,
) -> appwsrv_schema.CreateOrUpdateProviderResponse:
    """Update or create provider"""
    existing_provider = repository.find_provider(db_session, json.id)
    with db_session.persist(existing_provider or Provider()) as provider:
        provider.id = json.id
        provider.description = json.description
        provider.website_url = json.website_url
        provider.credentials_schema = json.credentials_schema
    return appwsrv_schema.CreateOrUpdateProviderResponse(
        provider=serializer.serialize_provider(provider)
    )


@providers_api.route("/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetProvidersResponse,
    ),
    operation_id="get_financial_data_providers",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_providers() -> appwsrv_schema.GetProvidersResponse:
    """Get providers"""
    return appwsrv_schema.GetProvidersResponse(
        providers=[
            serializer.serialize_provider(provider)
            for provider in db_session.query(Provider).all()
            if appwsrv_providers.is_provider_supported(provider)
        ]
    )


@providers_api.route("/<provider_id>/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetProviderResponse,
    ),
    operation_id="get_financial_data_provider",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_provider(provider_id: str) -> appwsrv_schema.GetProviderResponse:
    """Get provider"""
    provider = repository.find_provider(db_session, provider_id)
    if not provider:
        raise InvalidUserInput(f"Provider with id '${provider_id}' does not exist")
    return appwsrv_schema.GetProviderResponse(
        provider=serializer.serialize_provider(provider)
    )


@providers_api.route("/<provider_id>/", methods=["DELETE"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.DeleteProviderResponse,
    ),
    operation_id="delete_financial_data_provider",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def delete_provider(provider_id: str) -> appwsrv_schema.DeleteProviderResponse:
    """Delete provider"""
    provider = repository.get_provider(db_session, provider_id)
    linked_accounts: list[LinkedAccount] = provider.linked_accounts
    if len(linked_accounts) > 0:
        raise InvalidOperation("This provider is still in use")
    db_session.delete(provider)
    db_session.commit()
    logging.info(f"deleted provider_id={provider_id}")
    return appwsrv_schema.DeleteProviderResponse()


@providers_api.route("/plaid/settings/", methods=["GET"])
@jwt_required()
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.GetPlaidSettingsResponse,
    ),
    operation_id="get_plaid_settings",
    security=JWT_REQUIRED,
    tags=ENDPOINTS_TAGS,
)
def get_plaid_settings() -> appwsrv_schema.GetPlaidSettingsResponse:
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
