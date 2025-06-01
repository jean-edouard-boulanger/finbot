import enum
import re
import traceback
from typing import Annotated, Any, Callable, Pattern, Self, TypeAlias, TypeVar

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from pydantic_core import core_schema as pydantic_core_schema

from finbot.core.errors import ApplicationError, FinbotError
from finbot.core.utils import fully_qualified_type_name

CRYPTOCURRENCY_CODE_PREFIX = "X:"


class BaseModel(_BaseModel):
    model_config = ConfigDict(extra="forbid")


BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


class RegexValidatedStr(str):
    validation_regex: Pattern[str]
    examples: list[str]
    pre_formatters: list[Callable[[str], str]] | None = None

    @classmethod
    def __get_pydantic_core_schema__(cls, *_: Any) -> CoreSchema:
        return pydantic_core_schema.no_info_after_validator_function(
            cls.validate,
            pydantic_core_schema.str_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        json_schema = handler(schema)
        json_schema.update(
            pattern=cls.validation_regex.pattern,
            examples=cls.examples,
        )
        return json_schema

    @classmethod
    def validate(cls, v: str) -> Self:  # v is already validated as str by core_schema
        for formatter in cls.pre_formatters or []:
            v = formatter(v)
        if not cls.validation_regex.match(v):
            raise ValueError("invalid format")
        return cls(v)  # Remove f-string, just pass v directly


class CurrencyCode(RegexValidatedStr):
    validation_regex = re.compile("^[A-Z]{3}$")
    examples = ["EUR", "USD", "GBP"]
    pre_formatters = [str.upper]

    @property
    def raw_code(self) -> str:
        return self


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
        generic_user_message = "Internal error while processing request (please contact your system administrator)"
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


class GenericError(BaseModel):
    error: str
    code: str | None = None


class ApplicationErrorResponse(BaseModel):
    error: ApplicationErrorData

    @staticmethod
    def from_exception(e: Exception) -> "ApplicationErrorResponse":
        return ApplicationErrorResponse(error=ApplicationErrorData.from_exception(e))


class HealthRequest(BaseModel):
    pass


class HealthResponse(BaseModel):
    healthy: bool


HexColour = Annotated[str, Field(pattern=r"^#[A-Fa-f0-9]{6}$")]
LinkedAccountId: TypeAlias = int
