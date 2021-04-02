from finbot.apps.appwsrv.exceptions import Error, ApplicationError
from finbot.core import tracer

from flask import jsonify, request
from contextlib import contextmanager
from datetime import datetime, timedelta
import functools
import logging
import jsonschema
import stackprinter


class Route(object):
    def __init__(self, base=None):
        self.base = base

    def p(self, identifier):
        return Route(str(f"{self.base}/<{identifier}>"))

    def __getattr__(self, path):
        return Route(str(f"{self.base}/{path}"))

    def __call__(self):
        return str(self.base)


def log_time_elapsed(elapsed: timedelta):
    logging.info(f"time elapsed: {elapsed}")


@contextmanager
def time_elapsed(callback=log_time_elapsed):
    start = datetime.now()
    try:
        yield
    finally:
        callback(datetime.now() - start)


def make_error(user_message, debug_message=None, trace=None):
    return {
        "user_message": user_message,
        "debug_message": debug_message,
        "trace": trace,
    }


def make_error_response(user_message, debug_message=None, trace=None):
    return jsonify({"error": make_error(user_message, debug_message, trace)})


def _get_tracer_context(request_payload):
    if request_payload is None:
        return None
    data = request_payload.get(tracer.CONTEXT_TAG)
    if data is None:
        return None
    return tracer.FlatContext(**data)


def request_handler(trace_values=False, schema=None):
    def impl(func):
        @functools.wraps(func)
        def handler(*args, **kwargs):
            sp_trace_values = "all" if trace_values else None
            with time_elapsed():
                try:
                    logging.info(f"process {func.__name__} request")
                    payload = request.get_json(silent=True)
                    if schema:
                        try:
                            jsonschema.validate(instance=payload, schema=schema)
                        except jsonschema.ValidationError as e:
                            raise Error(f"failed to validate request: {e}")
                    flat_context = _get_tracer_context(payload)
                    with tracer.adopt(flat_context, func.__name__):
                        response = func(*args, **kwargs)
                        logging.info("request processed successfully")
                        return response
                except ApplicationError as e:
                    logging.warning(
                        "request processed with error:"
                        f" {e}\n{stackprinter.format(style='darkbg3', show_vals=sp_trace_values)}"
                    )
                    return make_error_response(
                        user_message=str(e),
                        debug_message=str(e),
                        trace=stackprinter.format(show_vals=sp_trace_values),
                    )
                except Exception as e:
                    logging.warning(
                        f"request processed with error:"
                        f" {e}\n{stackprinter.format(style='darkbg3', show_vals=sp_trace_values)}"
                    )
                    return make_error_response(
                        user_message="operation failed (unknown error)",
                        debug_message=str(e),
                        trace=stackprinter.format(show_vals=sp_trace_values),
                    )

        return handler

    return impl
