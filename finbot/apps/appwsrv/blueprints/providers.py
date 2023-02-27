import logging

from flask import Blueprint

from finbot.apps.appwsrv.blueprints.base import API_V1
from finbot.apps.appwsrv.db import db_session
from finbot.core.errors import InvalidOperation, InvalidUserInput
from finbot.core.web_service import RequestContext, Route, service_endpoint
from finbot.model import LinkedAccount, Provider, repository

logger = logging.getLogger(__name__)

PROVIDERS: Route = API_V1.providers
providers_api = Blueprint("providers_api", __name__)


@providers_api.route(PROVIDERS(), methods=["PUT"])
@service_endpoint(
    schema={
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "description", "website_url", "credentials_schema"],
        "properties": {
            "id": {"type": "string"},
            "description": {"type": "string"},
            "website_url": {"type": "string"},
            "credentials_schema": {"type": "object"},
        },
    }
)
def update_or_create_provider(request_context: RequestContext):
    data = request_context.request
    existing_provider = repository.find_provider(db_session, data["id"])
    with db_session.persist(existing_provider or Provider()) as provider:
        provider.id = data["id"]
        provider.description = data["description"]
        provider.website_url = data["website_url"]
        provider.credentials_schema = data["credentials_schema"]
    return {"provider": provider}


@providers_api.route(PROVIDERS(), methods=["GET"])
@service_endpoint()
def get_providers():
    providers = db_session.query(Provider).all()
    return {"providers": [provider for provider in providers]}


@providers_api.route(API_V1.providers.p("provider_id")(), methods=["GET"])
@service_endpoint()
def get_provider(provider_id: str):
    provider = repository.find_provider(db_session, provider_id)
    if not provider:
        raise InvalidUserInput(f"Provider with id '${provider_id}' does not exist")
    return {"provider": provider}


@providers_api.route(API_V1.providers.p("provider_id")(), methods=["DELETE"])
@service_endpoint()
def delete_provider(provider_id: str):
    provider = repository.get_provider(db_session, provider_id)
    linked_accounts: list[LinkedAccount] = provider.linked_accounts
    if len(linked_accounts) > 0:
        raise InvalidOperation("This provider is still in use")
    db_session.delete(provider)
    db_session.commit()
    logging.info(f"deleted provider_id={provider_id}")
    return {}
