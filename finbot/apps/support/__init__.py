from flask import jsonify
from contextlib import contextmanager
from datetime import datetime
import functools
import logging
import traceback


class Route(object):
    def __init__(self, base=None):
        self.base = base

    def p(self, identifier):
        return Route(str(f"{self.base}/<{identifier}>"))

    def __getattr__(self, path):
        return Route(str(f"{self.base}/{path}"))


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


def generic_request_handler(func):
    @functools.wraps(func)
    def impl(*args, **kwargs):
        with time_elapsed():
            try:
                logging.info(f"process {func.__name__} request")
                response = func(*args, **kwargs)
                logging.info("request processed successfully")
                return response
            except Exception as e:
                logging.warn(f"request processed with error: {e}\n{traceback.format_exc()}")
                return make_error_response(
                    user_message="system failure",
                    debug_message=str(e),
                    trace=traceback.format_exc()
                )
    return impl
