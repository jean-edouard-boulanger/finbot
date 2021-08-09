from finbot.core.utils import (
    fully_qualified_type_name,
    format_stack,
    scoped_stack_printer_configuration,
)
from finbot.core.errors import FinbotError, ApplicationError
from finbot.core.serialization import serialize, pretty_dump
from finbot.core import tracer

import jsonschema

from typing import Optional, Callable, Iterator, Any
from flask import jsonify, request
from contextlib import contextmanager
from datetime import datetime, timedelta
from dataclasses import dataclass
import functools
import logging


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


def service_endpoint(
    trace_values: bool = True, schema: Optional[dict[Any, Any]] = None
) -> Callable[..., Any]:
    def impl(func: Callable[..., Any]) -> Callable[..., Any]:
        def prepare_response(response_data: Any) -> Any:
            serialized_response = serialize(response_data)
            logging.debug(f"response_dump={pretty_dump(serialized_response)}")
            return jsonify(serialized_response)

        @functools.wraps(func)
        def handler(*args: Any, **kwargs: Any) -> Any:
            fs_show_vals = "all" if trace_values else None
            with time_elapsed():
                with scoped_stack_printer_configuration(show_vals=fs_show_vals):
                    try:
                        logging.info(f"process {func.__name__} request")
                        payload = request.get_json(silent=True)
                        if schema:
                            try:
                                jsonschema.validate(instance=payload, schema=schema)
                            except jsonschema.ValidationError as e:
                                raise RequestValidationError(
                                    f"failed to validate request: {e}"
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
