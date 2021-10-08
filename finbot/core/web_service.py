from finbot.core.utils import (
    fully_qualified_type_name,
    format_stack,
    scoped_stack_printer_configuration,
)
from finbot.core.errors import FinbotError, ApplicationError
from finbot.core.serialization import serialize, pretty_dump
from finbot.core import tracer

import jsonschema

from flask import jsonify, request
from flask import Response as FlaskResponse
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from werkzeug.datastructures import ImmutableMultiDict

from typing import Optional, Callable, Iterator, Any, TypedDict, Union, Type
from contextlib import contextmanager
from datetime import datetime, timedelta, date
from dataclasses import dataclass
import functools
import logging
import inspect


class Route(object):
    def __init__(self, base: Optional[str] = None) -> None:
        self.base = base or str()

    def p(self, identifier: str) -> "Route":
        return Route(str(f"{self.base}/<{identifier}>"))

    def __getattr__(self, path: str) -> "Route":
        return Route(str(f"{self.base}/{path}"))

    def __call__(self) -> str:
        return str(self.base)


def log_time_elapsed(elapsed: timedelta) -> None:
    logging.info(f"time elapsed: {elapsed}")


@contextmanager
def time_elapsed(
    callback: Callable[[timedelta], None] = log_time_elapsed
) -> Iterator[None]:
    start = datetime.now()
    try:
        yield
    finally:
        callback(datetime.now() - start)


def make_error(
    user_message: str, debug_message: Optional[str] = None, trace: Optional[str] = None
) -> dict[str, Optional[str]]:
    return {
        "user_message": user_message,
        "debug_message": debug_message,
        "trace": trace,
    }


def _get_tracer_context(request_payload: Optional[Any]) -> Optional[tracer.FlatContext]:
    if request_payload is None:
        return None
    if not isinstance(request_payload, dict):
        return None
    data = request_payload.get(tracer.CONTEXT_TAG)
    if data is None:
        return None
    return tracer.FlatContext(**data)


class RequestValidationError(FinbotError):
    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)


@dataclass
class ApplicationErrorData:
    user_message: str
    debug_message: Optional[str] = None
    error_code: Optional[str] = None
    exception_type: Optional[str] = None
    trace: Optional[str] = None
    distributed_trace_key: Optional[tracer.Step.Key] = None

    def serialize(self) -> dict[str, Any]:
        return {
            "user_message": self.user_message,
            "debug_message": self.debug_message,
            "error_code": self.error_code,
            "exception_type": self.exception_type,
            "trace": self.trace,
            "distributed_trace_key": self.distributed_trace_key,
        }

    @staticmethod
    def from_exception(e: Exception) -> "ApplicationErrorData":
        if isinstance(e, ApplicationError):
            return ApplicationErrorData(
                user_message=str(e),
                debug_message=str(e),
                error_code=e.error_code,
                exception_type=fully_qualified_type_name(e),
                trace=format_stack(e),
                distributed_trace_key=e.tracer_step_key,
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
                trace=format_stack(e),
                distributed_trace_key=e.tracer_step_key,
            )
        return ApplicationErrorData(
            user_message=generic_user_message,
            debug_message=str(e),
            error_code="X002",
            exception_type=fully_qualified_type_name(e),
            trace=format_stack(e),
            distributed_trace_key=tracer.current_key(),
        )


@dataclass
class ApplicationErrorResponse:
    error: ApplicationErrorData

    def serialize(self) -> dict[str, ApplicationErrorData]:
        return {"error": self.error}

    @staticmethod
    def from_exception(e: Exception) -> "ApplicationErrorResponse":
        return ApplicationErrorResponse(ApplicationErrorData.from_exception(e))


@dataclass
class RequestContext:
    _request_payload: Optional[dict[Any, Any]]
    _parameters: dict[str, Any]
    _user_id: Optional[int]

    @property
    def request(self) -> dict[Any, Any]:
        if self._request_payload is None:
            raise RuntimeError(
                "trying to access unset request payload in request context"
            )
        return self._request_payload

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    @property
    def user_id(self) -> int:
        if self._user_id is None:
            raise RuntimeError("trying to access unset user_id in request context")
        return self._user_id


def _get_jwt_identity_safe() -> Optional[int]:
    if verify_jwt_in_request(optional=True):
        jwt_ident: Optional[int] = get_jwt_identity()
        return jwt_ident
    return None


def _init_request_context(
    request_payload: Optional[dict[Any, Any]], parameters: dict[str, Any]
) -> RequestContext:
    return RequestContext(
        _request_payload=request_payload,
        _parameters=parameters,
        _user_id=_get_jwt_identity_safe(),
    )


ParameterType = Union[
    Type[str],
    Type[int],
    Type[float],
    Type[bool],
    Type[datetime],
    Type[date],
    Callable[[str], Any],
]


class ParameterDef(TypedDict, total=False):
    type: ParameterType
    required: bool
    default: Any


def _parse_raw_parameter_value(raw_value: str, parameter_type: ParameterType) -> Any:
    if parameter_type in {str, int, float}:
        return parameter_type(raw_value)  # type: ignore
    if parameter_type is bool:
        true_values = ["1", "true", "t", "y", "yes"]
        if raw_value.lower() in true_values:
            return True
        false_values = ["0", "false", "f", "n", "no"]
        if raw_value.lower() in false_values:
            return False
        raise RequestValidationError(
            f"bool parameter value expected to be any of:"
            f" {', '.join(true_values + false_values)}"
            f" (case insensitive)"
        )
    if parameter_type is datetime:
        return datetime.fromisoformat(raw_value)
    if parameter_type is date:
        return date.fromisoformat(raw_value)
    return parameter_type(raw_value)  # type: ignore


def _parse_url_parameter(
    parameter_name: str,
    parameter_def: ParameterDef,
    raw_arguments: ImmutableMultiDict[Any, Any],
) -> Optional[Any]:
    if parameter_def.get("required", False) and parameter_name not in raw_arguments:
        raise RequestValidationError(
            f"Mandatory parameter '{parameter_name}' missing in request"
        )
    raw_value = raw_arguments.get(parameter_name)
    if raw_value is None:
        if "default" in parameter_def:
            return parameter_def["default"]
        return None
    try:
        return _parse_raw_parameter_value(raw_value, parameter_def["type"])
    except Exception as e:
        raise RequestValidationError(
            f"Could not validate request parameter '{parameter_name}': {e}"
        )


def _parse_url_parameters(
    parameters_def: Optional[dict[str, ParameterDef]],
    raw_parameters: ImmutableMultiDict[Any, Any],
) -> dict[str, Optional[Any]]:
    parameters_def = parameters_def or {}
    for param_name in raw_parameters:
        if param_name not in parameters_def:
            raise RequestValidationError(
                f"Received unexpected parameter '{param_name}'"
            )
    return {
        param_name: _parse_url_parameter(param_name, param_def, raw_parameters)
        for param_name, param_def in parameters_def.items()
    }


def service_endpoint(
    trace_values: bool = True,
    schema: Optional[dict[Any, Any]] = None,
    parameters: Optional[dict[Any, ParameterDef]] = None,
) -> Callable[..., Any]:
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

        include_request_context = (
            "request_context" in inspect.signature(func).parameters
        )

        @functools.wraps(func)
        def handler(*args: Any, **kwargs: Any) -> Any:
            fs_show_vals = "all" if trace_values else None
            with time_elapsed():
                with scoped_stack_printer_configuration(show_vals=fs_show_vals):
                    try:
                        logging.info(
                            f"process {func.__name__} request route={request.full_path}"
                        )
                        payload = request.get_json(silent=True)
                        if schema:
                            try:
                                jsonschema.validate(instance=payload, schema=schema)
                            except jsonschema.ValidationError as e:
                                raise RequestValidationError(
                                    f"failed to validate request: {e}"
                                )
                        parsed_parameters = _parse_url_parameters(
                            parameters, request.args
                        )
                        if include_request_context:
                            logging.debug("initializing request context")
                            kwargs["request_context"] = _init_request_context(
                                payload, parsed_parameters
                            )
                        flat_context = _get_tracer_context(payload)
                        with tracer.adopt(flat_context, func.__name__):
                            response = func(*args, **kwargs)
                            logging.info("request processed successfully")
                            return prepare_response(response)
                    except Exception as e:
                        logging.warning(
                            "error while processing request:"
                            f" {e}\n{format_stack(style='darkbg3')}"
                        )
                        return prepare_response(
                            ApplicationErrorResponse.from_exception(e)
                        )

        return handler

    return impl
