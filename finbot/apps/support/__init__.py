from flask import jsonify, request
from contextlib import contextmanager
from datetime import datetime
import functools
import logging
import traceback
import jsonschema


class Route(object):
    def __init__(self, base=None):
        self.base = base

    def p(self, identifier):
        return Route(str(f"{self.base}/<{identifier}>"))

    def __getattr__(self, path):
        return Route(str(f"{self.base}/{path}"))

    @property
    def _(self):
        return str(self.base)


def log_time_elapsed(time_elapsed):
    logging.info(f"time elapsed: {time_elapsed}")


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
        "trace": trace
    }


def make_error_response(user_message, debug_message=None, trace=None):
    return jsonify({"error": make_error(user_message, debug_message, trace)})


class Error(RuntimeError):
    pass


class ApplicationError(Error):
    pass


def generic_request_handler(schema=None):
    def impl(func):
        @functools.wraps(func)
        def handler(*args, **kwargs):
            with time_elapsed():
                try:
                    logging.info(f"process {func.__name__} request")
                    if schema:
                        try:
                            request_data = request.json
                            jsonschema.validate(instance=request_data, schema=schema)
                        except jsonschema.ValidationError as e:
                            raise Error(f"failed to validate request: {e}")
                    response = func(*args, **kwargs)
                    logging.info("request processed successfully")
                    return response
                except ApplicationError as e:
                    logging.warn(f"request processed with error: {e}\n{traceback.format_exc()}")
                    return make_error_response(
                        user_message=str(e),
                        debug_message=str(e),
                        trace=traceback.format_exc())
                except Exception as e:
                    logging.warn(f"request processed with error: {e}\n{traceback.format_exc()}")
                    return make_error_response(
                        user_message="operation failed (unknown error)",
                        debug_message=str(e),
                        trace=traceback.format_exc())
        return handler
    return impl
