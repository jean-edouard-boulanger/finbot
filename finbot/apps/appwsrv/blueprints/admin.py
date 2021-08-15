from finbot.apps.appwsrv.blueprints import API_V1
from finbot.apps.appwsrv.db import db_session
from finbot.core.web_service import Route, service_endpoint, RequestContext
from finbot.core import tracer
from finbot.model import DistributedTrace

from flask import Blueprint


ADMIN: Route = API_V1.admin
admin_api = Blueprint("admin_api", __name__)


@admin_api.route(ADMIN.traces.p("string:guid")(), methods=["GET"])
@service_endpoint(parameters={"format": {"type": str, "default": "list"}})
def get_traces(request_context: RequestContext, guid: str):
    trace_format = request_context.parameters["format"]
    traces = db_session.query(DistributedTrace).filter_by(guid=guid).all()
    if trace_format == "tree":
        return {"tree": tracer.build_tree(traces)}
    return {"traces": [trace for trace in traces]}
