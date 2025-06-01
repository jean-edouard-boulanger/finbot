from fastapi import FastAPI

from finbot.apps.appwsrv.routes.admin import router as admin_router
from finbot.apps.appwsrv.routes.auth import router as auth_router
from finbot.apps.appwsrv.routes.base import router as base_router
from finbot.apps.appwsrv.routes.formatting_rules import router as formatting_rules_router
from finbot.apps.appwsrv.routes.linked_accounts import router as linked_accounts_router
from finbot.apps.appwsrv.routes.linked_accounts_valuation import router as linked_accounts_valuation_router
from finbot.apps.appwsrv.routes.providers import router as providers_router
from finbot.apps.appwsrv.routes.reports import router as reports_router
from finbot.apps.appwsrv.routes.user_account_valuation import router as user_account_valuation_router
from finbot.apps.appwsrv.routes.user_accounts import router as user_accounts_router
from finbot.apps.http_base import ORJSONResponse, setup_app
from finbot.core import environment
from finbot.core.logging import configure_logging

configure_logging(environment.get_desired_log_level())

app = FastAPI(
    root_path="/api/v1",
    default_response_class=ORJSONResponse,
    title="Finbot application service",
    description="API documentation for appwsrv",
)
setup_app(app)

app.include_router(admin_router)
app.include_router(base_router)
app.include_router(auth_router)
app.include_router(providers_router)
app.include_router(user_account_valuation_router)
app.include_router(user_accounts_router)
app.include_router(linked_accounts_valuation_router)
app.include_router(linked_accounts_router)
app.include_router(reports_router)
app.include_router(formatting_rules_router)
