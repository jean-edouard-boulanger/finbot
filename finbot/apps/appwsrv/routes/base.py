from fastapi import APIRouter

from finbot._version import __api_version__, __version__
from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.core import environment
from finbot.core import schema as core_schema

router = APIRouter(
    tags=["System"],
)


@router.get(
    "/healthy/",
    operation_id="is_healthy",
)
def healthy() -> core_schema.HealthResponse:
    """Is server healthy"""
    return core_schema.HealthResponse(healthy=True)


@router.get(
    "/system_report/",
    operation_id="get_system_report",
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
