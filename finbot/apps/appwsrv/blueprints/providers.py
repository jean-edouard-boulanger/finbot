import logging

from flask import Blueprint

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.db import db_session
from finbot.core.errors import InvalidOperation, InvalidUserInput
from finbot.core.web_service import jwt_required, service_endpoint, validate
from finbot.model import LinkedAccount, Provider, repository

logger = logging.getLogger(__name__)

providers_api = Blueprint(
    name="providers_api", import_name=__name__, url_prefix=f"{API_URL_PREFIX}/providers"
)


@providers_api.route("/", methods=["PUT"])
@jwt_required()
@service_endpoint()
@validate()
def update_or_create_provider(
    body: appwsrv_schema.CreateOrUpdateProviderRequest,
) -> appwsrv_schema.CreateOrUpdateProviderResponse:
    existing_provider = repository.find_provider(db_session, body.id)
    with db_session.persist(existing_provider or Provider()) as provider:
        provider.id = body.id
        provider.description = body.description
        provider.website_url = body.website_url
        provider.credentials_schema = body.credentials_schema
    return appwsrv_schema.CreateOrUpdateProviderResponse(
        provider=serializer.serialize_provider(provider)
    )


@providers_api.route("/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_providers() -> appwsrv_schema.GetProvidersResponse:
    return appwsrv_schema.GetProvidersResponse(
        providers=[
            serializer.serialize_provider(provider)
            for provider in db_session.query(Provider).all()
        ]
    )


@providers_api.route("/<provider_id>/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_provider(provider_id: str) -> appwsrv_schema.GetProviderResponse:
    provider = repository.find_provider(db_session, provider_id)
    if not provider:
        raise InvalidUserInput(f"Provider with id '${provider_id}' does not exist")
    return appwsrv_schema.GetProviderResponse(
        provider=serializer.serialize_provider(provider)
    )


@providers_api.route("/<provider_id>/", methods=["DELETE"])
@jwt_required()
@service_endpoint()
@validate()
def delete_provider(provider_id: str) -> appwsrv_schema.DeleteProviderResponse:
    provider = repository.get_provider(db_session, provider_id)
    linked_accounts: list[LinkedAccount] = provider.linked_accounts
    if len(linked_accounts) > 0:
        raise InvalidOperation("This provider is still in use")
    db_session.delete(provider)
    db_session.commit()
    logging.info(f"deleted provider_id={provider_id}")
    return appwsrv_schema.DeleteProviderResponse()
