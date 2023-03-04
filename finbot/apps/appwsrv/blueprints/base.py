from flask import Blueprint

from finbot._version import __version__
from finbot.core import environment
from finbot.core.web_service import Route

API_V1 = Route("/api/v1")
base_api = Blueprint("api", __name__)


@base_api.route(API_V1.healthy(), methods=["GET"])
def healthy():
    return {"healthy": True}


@base_api.route(API_V1.system_report(), methods=["GET"])
def get_system_report():
    return {
        "system_report": {
            "finbot_version": __version__,
            "runtime": environment.get_finbot_runtime(),
        }
    }
