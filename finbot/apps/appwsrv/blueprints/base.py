from flask import Blueprint

from finbot._version import __api_version__, __version__
from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv.spec import spec
from finbot.core import environment
from finbot.core import schema as core_schema
from finbot.core.spec_tree import ResponseSpec
from finbot.core.web_service import service_endpoint

API_URL_PREFIX = "/api/v1"
base_api = Blueprint(name="api", import_name=__name__, url_prefix=f"{API_URL_PREFIX}/")


ENDPOINTS_TAGS = ["System"]


@base_api.route("/healthy/", methods=["GET"])
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=core_schema.HealthResponse,
    ),
    operation_id="is_healthy",
    tags=ENDPOINTS_TAGS,
)
def healthy() -> core_schema.HealthResponse:
    """Is server healthy"""
    return core_schema.HealthResponse(healthy=True)


@base_api.route("/system_report/", methods=["GET"])
@service_endpoint()
@spec.validate(
    resp=ResponseSpec(
        HTTP_200=appwsrv_schema.SystemReportResponse,
    ),
    operation_id="get_system_report",
    tags=ENDPOINTS_TAGS,
)
def get_system_report() -> appwsrv_schema.SystemReportResponse:
    """Get system report"""
    return appwsrv_schema.SystemReportResponse(
        system_report=appwsrv_schema.SystemReport(
            finbot_version=__version__,
            finbot_api_version=__api_version__,
            runtime=environment.get_finbot_runtime(),
            is_demo=environment.is_demo(),
        )
    )
