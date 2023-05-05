from flask import Blueprint

from finbot._version import __version__
from finbot.core import environment

API_URL_PREFIX = "/api/v1/"
base_api = Blueprint(name="api", import_name=__name__, url_prefix=API_URL_PREFIX)


@base_api.route("/healthy/", methods=["GET"])
def healthy():
    return {"healthy": True}


@base_api.route("/system_report/", methods=["GET"])
def get_system_report():
    return {
        "system_report": {
            "finbot_version": __version__,
            "runtime": environment.get_finbot_runtime(),
        }
    }
