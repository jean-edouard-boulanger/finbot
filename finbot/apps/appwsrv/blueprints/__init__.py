from finbot.apps.appwsrv.blueprints.admin import ADMIN, admin_api
from finbot.apps.appwsrv.blueprints.auth import AUTH, auth_api
from finbot.apps.appwsrv.blueprints.base import API_V1, base_api
from finbot.apps.appwsrv.blueprints.linked_accounts import (
    LINKED_ACCOUNT,
    LINKED_ACCOUNTS,
    linked_accounts_api,
)
from finbot.apps.appwsrv.blueprints.providers import PROVIDERS, providers_api
from finbot.apps.appwsrv.blueprints.reports import REPORTS, reports_api
from finbot.apps.appwsrv.blueprints.user_accounts import (
    ACCOUNT,
    ACCOUNTS,
    user_accounts_api,
)
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
