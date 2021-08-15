from finbot.apps.appwsrv.db import db_session
from finbot.apps.appwsrv.blueprints import (
    base_api,
    admin_api,
    auth_api,
    providers_api,
    user_accounts_api,
    linked_accounts_api,
    reports_api,
    valuation_api,
)
from finbot.core.logging import configure_logging
from finbot.core import environment

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager


# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = environment.get_secret_key()

CORS(app)
JWTManager(app)


@app.teardown_appcontext
def cleanup_context(*args, **kwargs):
    db_session.remove()


app.register_blueprint(base_api)
app.register_blueprint(admin_api)
app.register_blueprint(auth_api)
app.register_blueprint(providers_api)
app.register_blueprint(user_accounts_api)
app.register_blueprint(linked_accounts_api)
app.register_blueprint(reports_api)
app.register_blueprint(valuation_api)
