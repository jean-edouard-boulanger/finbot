import os
from dataclasses import dataclass
from typing import Type, TypeVar, Union


class MissingEnvironment(RuntimeError):
    pass


class _Raises(object):
    pass


@dataclass
class Environment:
    secret_key: str
    database_url: str
    finbotwsrv_endpoint: str
    snapwsrv_endpoint: str
    histwsrv_endpoint: str
    appwsrv_endpoint: str
    webapp_endpoint: str
    runtime: str
    rmq_url: str

    @property
    def desired_log_level(self) -> str:
        return "DEBUG" if self.runtime == "development" else "DEBUG"


T = TypeVar("T")


def get_environment_value(
    name: str, default: Union[str, Type[_Raises]] = _Raises
) -> str:
    value = os.environ.get(name, default)
    if value == _Raises:
        raise MissingEnvironment(f"environment variable {name} not available")
    return str(value)


def get_secret_key() -> str:
    return get_environment_value("FINBOT_SECRET_KEY")


def get_database_url() -> str:
    db_user = get_environment_value("FINBOT_DB_USER")
    db_password = get_environment_value("FINBOT_DB_PASSWORD")
    db_hostname = get_environment_value("FINBOT_DB_HOSTNAME")
    db_port = get_environment_value("FINBOT_DB_PORT")
    db_name = get_environment_value("FINBOT_DB_DBNAME")
    return f"postgresql+psycopg2://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"


def get_finbotwsrv_endpoint() -> str:
    return get_environment_value("FINBOT_FINBOTWSRV_ENDPOINT")


def get_snapwsrv_endpoint() -> str:
    return get_environment_value("FINBOT_SNAPWSRV_ENDPOINT")


def get_histwsrv_endpoint() -> str:
    return get_environment_value("FINBOT_HISTWSRV_ENDPOINT")


def get_appwsrv_endpoint() -> str:
    return get_environment_value("FINBOT_APPWSRV_ENDPOINT")


def get_webapp_endpoint() -> str:
    return get_environment_value("FINBOT_WEBAPP_ENDPOINT")


def get_finbot_runtime() -> str:
    return get_environment_value("FINBOT_ENV", "production")


def get_rmq_url() -> str:
    rmq_hostname = get_environment_value("FINBOT_RMQ_HOSTNAME")
    rmq_port = get_environment_value("FINBOT_RMQ_PORT")
    rmq_user = get_environment_value("FINBOT_RMQ_USER")
    rmq_password = get_environment_value("FINBOT_RMQ_PASSWORD")
    return f"amqp://{rmq_user}:{rmq_password}@{rmq_hostname}:{rmq_port}"


def get() -> Environment:
    return Environment(
        secret_key=get_secret_key(),
        database_url=get_database_url(),
        finbotwsrv_endpoint=get_finbotwsrv_endpoint(),
        snapwsrv_endpoint=get_snapwsrv_endpoint(),
        histwsrv_endpoint=get_histwsrv_endpoint(),
        appwsrv_endpoint=get_appwsrv_endpoint(),
        webapp_endpoint=get_webapp_endpoint(),
        runtime=get_finbot_runtime(),
        rmq_url=get_rmq_url(),
    )
