import logging
import os
from dataclasses import dataclass
from typing import TypeVar, cast

logger = logging.getLogger(__name__)

PRODUCTION_ENV = "production"
DEVELOPMENT_ENV = "development"


class MissingEnvironment(RuntimeError):
    pass


class _Raise(object):
    pass


@dataclass(frozen=True)
class PlaidEnvironment:
    environment: str
    client_id: str
    public_key: str
    secret_key: str


@dataclass(frozen=True)
class Environment:
    secret_key: str
    jwt_secret_key: str
    database_url: str
    finbotwsrv_endpoint: str
    appwsrv_endpoint: str
    webapp_endpoint: str
    runtime: str
    rmq_url: str
    freecurrencyapi_key: str
    saxo_gateway_url: str | None
    plaid_environment: PlaidEnvironment | None

    @property
    def is_production(self) -> bool:
        return self.runtime == PRODUCTION_ENV

    @property
    def desired_log_level(self) -> str:
        return "INFO" if self.runtime == PRODUCTION_ENV else "DEBUG"


T = TypeVar("T")


def get_environment_value(name: str) -> str:
    value = os.environ.get(name, _Raise)
    if value == _Raise:
        raise MissingEnvironment(f"{name}")
    return str(value)


def get_environment_value_or(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def get_secret_key() -> str:
    return get_environment_value("FINBOT_SECRET_KEY")


def get_jwt_secret_key() -> str:
    return get_environment_value("FINBOT_JWT_SECRET_KEY")


def get_database_url() -> str:
    db_user = get_environment_value("FINBOT_DB_USER")
    db_password = get_environment_value("FINBOT_DB_PASSWORD")
    db_hostname = get_environment_value("FINBOT_DB_HOSTNAME")
    db_port = get_environment_value("FINBOT_DB_PORT")
    db_name = get_environment_value("FINBOT_DB_DBNAME")
    return f"postgresql+psycopg2://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"


def get_finbotwsrv_endpoint() -> str:
    return get_environment_value("FINBOT_FINBOTWSRV_ENDPOINT")


def get_appwsrv_endpoint() -> str:
    return get_environment_value("FINBOT_APPWSRV_ENDPOINT")


def get_webapp_endpoint() -> str:
    return get_environment_value("FINBOT_WEBAPP_ENDPOINT")


def get_web_service_endpoint(service_name: str) -> str:
    return get_environment_value(f"FINBOT_{service_name.upper()}_ENDPOINT")


def get_saxo_gateway_url() -> str | None:
    return get_environment_value_or("FINBOT_SAXO_GATEWAY_URL", None)


def get_finbot_runtime() -> str:
    env_var_name = "FINBOT_ENV"
    raw_value = get_environment_value_or(env_var_name, PRODUCTION_ENV)
    if raw_value not in (DEVELOPMENT_ENV, PRODUCTION_ENV):
        logger.warning(
            f"got bad value for '{env_var_name}' (expected {DEVELOPMENT_ENV} or {PRODUCTION_ENV}),"
            f" defaulting to '{DEVELOPMENT_ENV}'"
        )
        return PRODUCTION_ENV
    return raw_value


def get_freecurrencyapi_key() -> str:
    return get_environment_value("FINBOT_FREECURRENCYAPI_KEY")


def get_plaid_environment() -> PlaidEnvironment | None:
    payload = {
        "environment": get_environment_value_or("FINBOT_PLAID_ENVIRONMENT"),
        "client_id": get_environment_value_or("FINBOT_PLAID_CLIENT_ID"),
        "public_key": get_environment_value_or("FINBOT_PLAID_PUBLIC_KEY"),
        "secret_key": get_environment_value_or("FINBOT_PLAID_SECRET_KEY"),
    }
    is_configured = all(value for value in payload.values())
    return PlaidEnvironment(**cast(dict[str, str], payload)) if is_configured else None


def is_plaid_configured() -> bool:
    return get_plaid_environment() is not None


def is_saxo_configured() -> bool:
    return get_saxo_gateway_url() is not None


def is_production() -> bool:
    return get_finbot_runtime() == PRODUCTION_ENV


def get_rmq_url() -> str:
    rmq_hostname = get_environment_value("FINBOT_RMQ_HOSTNAME")
    rmq_port = get_environment_value("FINBOT_RMQ_PORT")
    rmq_user = get_environment_value("FINBOT_RMQ_USER")
    rmq_password = get_environment_value("FINBOT_RMQ_PASSWORD")
    return f"amqp://{rmq_user}:{rmq_password}@{rmq_hostname}:{rmq_port}"


def get() -> Environment:
    return Environment(
        secret_key=get_secret_key(),
        jwt_secret_key=get_jwt_secret_key(),
        database_url=get_database_url(),
        finbotwsrv_endpoint=get_finbotwsrv_endpoint(),
        appwsrv_endpoint=get_appwsrv_endpoint(),
        webapp_endpoint=get_webapp_endpoint(),
        runtime=get_finbot_runtime(),
        rmq_url=get_rmq_url(),
        freecurrencyapi_key=get_freecurrencyapi_key(),
        saxo_gateway_url=get_saxo_gateway_url(),
        plaid_environment=get_plaid_environment(),
    )
