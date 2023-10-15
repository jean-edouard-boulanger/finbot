import enum
import traceback
from typing import Annotated, Any, TypeAlias

from pydantic import BaseModel as _BaseModel
from pydantic import Extra, Field

from finbot.core.errors import ApplicationError, FinbotError
from finbot.core.utils import fully_qualified_type_name


class BaseModel(_BaseModel):
    class Config:
        extra = Extra.forbid


class ValuationFrequency(str, enum.Enum):
    Daily = "Daily"
    Weekly = "Weekly"
    Monthly = "Monthly"
    Quarterly = "Quarterly"
    Yearly = "Yearly"


class ValuationChange(BaseModel):
    change_1hour: float | None
    change_1day: float | None
    change_1week: float | None
    change_1month: float | None
    change_6months: float | None
    change_1year: float | None
    change_2years: float | None


CredentialsPayloadType: TypeAlias = dict[str, Any]


class ApplicationErrorData(BaseModel):
    user_message: str
    debug_message: str | None = None
    error_code: str | None = None
    exception_type: str | None = None
    trace: str | None = None

    @staticmethod
    def from_exception(e: Exception) -> "ApplicationErrorData":
        if isinstance(e, ApplicationError):
            return ApplicationErrorData(
                user_message=str(e),
                debug_message=str(e),
                error_code=e.error_code,
                exception_type=fully_qualified_type_name(e),
                trace=traceback.format_exc(),
            )
        generic_user_message = (
            "Internal error while processing request "
            "(please contact your system administrator)"
        )
        if isinstance(e, FinbotError):
            return ApplicationErrorData(
                user_message=generic_user_message,
                debug_message=str(e),
                error_code="X001",
                exception_type=fully_qualified_type_name(e),
                trace=traceback.format_exc(),
            )
        return ApplicationErrorData(
            user_message=generic_user_message,
            debug_message=str(e),
            error_code="X002",
            exception_type=fully_qualified_type_name(e),
            trace=traceback.format_exc(),
        )


class ApplicationErrorResponse(BaseModel):
    error: ApplicationErrorData

    @staticmethod
    def from_exception(e: Exception) -> "ApplicationErrorResponse":
        return ApplicationErrorResponse(error=ApplicationErrorData.from_exception(e))


class HealthRequest(BaseModel):
    pass


class HealthResponse(BaseModel):
    healthy: bool


HexColour = Annotated[str, Field(regex=r"^#[A-Fa-f0-9]{6}$")]
