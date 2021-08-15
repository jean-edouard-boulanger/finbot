from finbot.core.web_service import Route

from flask import Blueprint


API_V1 = Route("/api/v1")
base_api = Blueprint("api", __name__)


@base_api.route(API_V1.healthy(), methods=["GET"])
def healthy():
    return {"healthy": True}
