from dataclasses import dataclass
from pathlib import Path
import os


class MissingEnvironment(RuntimeError):
    pass


class _Raises(object):
    pass


@dataclass
class Environment:
    vault_path: Path
    secret_path: Path
    account_path: Path
    database_url: str
    finbotwsrv_endpoint: str
    snapwsrv_endpoint: str
    histwsrv_endpoint: str
    appwsrv_endpoint: str
    webapp_endpoint: str
    schedsrv_port: int
    schedsrv_endpoint: str


def get_environment_value(name: str, default: str = _Raises) -> str:
    value = os.environ.get(name, default)
    if value == _Raises:
        raise MissingEnvironment(f"environment variable {name} not available")
    return value


def get_vault_path() -> Path:
    return Path(get_environment_value("FINBOT_VAULT_PATH"))


def get_secret_path() -> Path:
    return Path(get_environment_value("FINBOT_SECRET_PATH"))


def get_account_path() -> Path:
    return Path(get_environment_value("FINBOT_ACCOUNT_PATH"))


def get_database_url() -> str:
    return get_environment_value("FINBOT_DB_URL")


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


def get_schedsrv_port() -> int:
    return int(get_environment_value("FINBOT_SCHEDSRV_PORT"))


def get_schedsrv_endpoint() -> str:
    return get_environment_value("FINBOT_SCHEDSRV_ENDPOINT")


def get() -> Environment:
    return Environment(
        vault_path=get_vault_path(),
        secret_path=get_secret_path(),
        account_path=get_account_path(),
        database_url=get_database_url(),
        finbotwsrv_endpoint=get_finbotwsrv_endpoint(),
        snapwsrv_endpoint=get_snapwsrv_endpoint(),
        histwsrv_endpoint=get_histwsrv_endpoint(),
        appwsrv_endpoint=get_appwsrv_endpoint(),
        webapp_endpoint=get_webapp_endpoint(),
        schedsrv_port=get_schedsrv_port(),
        schedsrv_endpoint=get_schedsrv_endpoint()
    )
