from typing import Any

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from finbot.apps.appwsrv.blueprints import (
    admin_api,
    auth_api,
    base_api,
    formatting_rules_api,
    linked_accounts_api,
    linked_accounts_valuation_api,
    providers_api,
    reports_api,
    user_account_valuation_api,
    user_accounts_api,
)
from finbot.apps.appwsrv.db import db_session
from finbot.core import environment
from finbot.core.logging import configure_logging

FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = FINBOT_ENV.jwt_secret_key

CORS(app)
JWTManager(app)


@app.teardown_appcontext
def cleanup_context(*args: Any, **kwargs: Any) -> None:
    db_session.remove()


app.register_blueprint(base_api)
app.register_blueprint(admin_api)
app.register_blueprint(auth_api)
app.register_blueprint(providers_api)
app.register_blueprint(user_accounts_api)
app.register_blueprint(linked_accounts_api)
app.register_blueprint(reports_api)
app.register_blueprint(user_account_valuation_api)
app.register_blueprint(linked_accounts_valuation_api)
app.register_blueprint(formatting_rules_api)
