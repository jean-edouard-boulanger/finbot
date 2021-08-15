from finbot.apps.appwsrv.blueprints.base import base_api, API_V1
from finbot.apps.appwsrv.blueprints.admin import admin_api, ADMIN
from finbot.apps.appwsrv.blueprints.auth import auth_api, AUTH
from finbot.apps.appwsrv.blueprints.providers import providers_api, PROVIDERS
from finbot.apps.appwsrv.blueprints.user_accounts import (
    user_accounts_api,
    ACCOUNT,
    ACCOUNTS,
)
from finbot.apps.appwsrv.blueprints.linked_accounts import (
    linked_accounts_api,
    LINKED_ACCOUNT,
    LINKED_ACCOUNTS,
)
from finbot.apps.appwsrv.blueprints.reports import reports_api, REPORTS
from finbot.apps.appwsrv.blueprints.valuation import valuation_api


__all__ = [
    "API_V1",
    "ADMIN",
    "AUTH",
    "ACCOUNT",
    "ACCOUNTS",
    "PROVIDERS",
    "LINKED_ACCOUNT",
    "LINKED_ACCOUNTS",
    "REPORTS",
    "base_api",
    "admin_api",
    "auth_api",
    "providers_api",
    "user_accounts_api",
    "linked_accounts_api",
    "reports_api",
    "valuation_api",
]
