import functools
import logging
import traceback
from typing import Any, Callable, ParamSpec, TypeVar, cast

from flask import Response as FlaskResponse
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from flask_pydantic import validate as _validate
from pydantic import BaseModel

from finbot.core.errors import ApplicationError, FinbotError
from finbot.core.serialization import pretty_dump, serialize
from finbot.core.utils import fully_qualified_type_name


class RequestValidationError(FinbotError):
    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)


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


def get_user_account_id() -> int:
    user_account_id = get_jwt_identity()
    assert isinstance(user_account_id, int)
    return user_account_id


def service_endpoint() -> Callable[..., Any]:
    def impl(func: Callable[..., Any]) -> Callable[..., Any]:
        def prepare_response(response_data: Any) -> Any:
            if isinstance(response_data, FlaskResponse):
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    logging.debug(
                        f"response_dump={pretty_dump(response_data.get_json(silent=True))}"
                    )
                return response_data
            serialized_response = serialize(response_data)
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"response_dump={pretty_dump(serialized_response)}")
            return jsonify(serialized_response)

        @functools.wraps(func)
        def handler(*args: Any, **kwargs: Any) -> Any:
            try:
                logging.info(
                    f"process {func.__name__} request route={request.full_path}"
                )
                response = func(*args, **kwargs)
                logging.info("request processed successfully")
                return prepare_response(response)
            except Exception as e:
                logging.warning(
                    "error while processing request:" f" {e}\n{traceback.format_exc()}"
                )
                return prepare_response(ApplicationErrorResponse.from_exception(e))

        return handler

    return impl


RT = TypeVar("RT")
P = ParamSpec("P")


def validate(
    body: type[BaseModel] | None = None,
    query: type[BaseModel] | None = None,
    on_success_status: int = 200,
    exclude_none: bool = False,
    response_many: bool = False,
    request_body_many: bool = False,
    response_by_alias: bool = False,
    get_json_params: dict[str, Any] | None = None,
    form: type[BaseModel] | None = None,
) -> Callable[[Callable[P, RT]], Callable[P, FlaskResponse]]:
    return cast(
        Callable[[Callable[P, RT]], Callable[P, FlaskResponse]],
        _validate(
            body=body,
            query=query,
            on_success_status=on_success_status,
            exclude_none=exclude_none,
            response_many=response_many,
            request_body_many=request_body_many,
            response_by_alias=response_by_alias,
            get_json_params=get_json_params,
            form=form,
        ),
    )
