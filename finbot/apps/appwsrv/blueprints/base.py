from flask import Blueprint

from finbot._version import __version__
from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.core import environment
from finbot.core import schema as core_schema
from finbot.core.web_service import service_endpoint, validate

API_URL_PREFIX = "/api/v1/"
base_api = Blueprint(name="api", import_name=__name__, url_prefix=API_URL_PREFIX)


@base_api.route("/healthy/", methods=["GET"])
@service_endpoint()
@validate()
def healthy() -> core_schema.HealthResponse:
    return core_schema.HealthResponse(healthy=True)


@base_api.route("/system_report/", methods=["GET"])
@service_endpoint()
@validate()
def get_system_report() -> appwsrv_schema.SystemReportResponse:
    return appwsrv_schema.SystemReportResponse(
        system_report=appwsrv_schema.SystemReport(
            finbot_version=__version__, runtime=environment.get_finbot_runtime()
        )
    )
