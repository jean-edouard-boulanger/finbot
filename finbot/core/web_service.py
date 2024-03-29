import functools
import logging
import traceback
import typing as t
from http import HTTPStatus
from typing import Any, Callable, Optional, ParamSpec, Self, TypeVar, cast

import flask
import orjson
import requests
import requests.exceptions
from flask import Response as FlaskResponse
from flask import jsonify, request
from flask.json.provider import DefaultJSONProvider
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required as _jwt_required
from flask_jwt_extended.view_decorators import LocationType
from werkzeug.exceptions import HTTPException

from finbot.core import environment
from finbot.core import schema as core_schema
from finbot.core.errors import FinbotError
from finbot.core.schema import ApplicationErrorData, ApplicationErrorResponse
from finbot.core.serialization import serialize


class RequestValidationError(FinbotError):
    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)


def get_user_account_id() -> int:
    user_account_id = get_jwt_identity()
    assert isinstance(user_account_id, int)
    return user_account_id


RT = TypeVar("RT")
P = ParamSpec("P")


def service_endpoint() -> Callable[[Callable[P, RT]], Callable[P, FlaskResponse]]:
    def impl(func: Callable[P, RT]) -> Callable[P, FlaskResponse]:
        def prepare_response(
            response_data: RT | FlaskResponse | ApplicationErrorResponse,
        ) -> FlaskResponse:
            if isinstance(response_data, FlaskResponse):
                return response_data
            serialized_response = serialize(response_data)
            return cast(FlaskResponse, jsonify(serialized_response))

        @functools.wraps(func)
        def handler(*args: P.args, **kwargs: P.kwargs) -> FlaskResponse:
            try:
                logging.info(f"process {func.__name__} request route={request.full_path}")
                response = func(*args, **kwargs)
                logging.debug("request processed successfully")
                return prepare_response(response)
            except HTTPException:
                raise
            except Exception as e:
                logging.warning("error while processing request:" f" {e}\n{traceback.format_exc()}")
                return cast(
                    FlaskResponse,
                    flask.current_app.response_class(
                        ApplicationErrorResponse.from_exception(e).json(),
                        status=HTTPStatus.INTERNAL_SERVER_ERROR,
                        content_type="application/json",
                    ),
                )

        return handler

    return impl


def jwt_required(
    optional: bool = False,
    fresh: bool = False,
    refresh: bool = False,
    locations: LocationType = None,
    verify_type: bool = True,
) -> Callable[[Callable[P, RT]], Callable[P, RT]]:
    return cast(
        Callable[[Callable[P, RT]], Callable[P, RT]],
        _jwt_required(
            optional=optional,
            fresh=fresh,
            refresh=refresh,
            locations=locations,
            verify_type=verify_type,
        ),
    )


class WebServiceClientError(FinbotError):
    pass


class WebServiceApplicationError(WebServiceClientError):
    def __init__(self, error_message: str, error: ApplicationErrorData):
        super().__init__(error_message)
        self.error = error


class WebServiceClient(object):
    service_name: str

    def __init__(self, server_endpoint: str):
        self._endpoint = server_endpoint

    def send_request(self, verb: str, route: str, payload: Optional[Any] = None) -> Any:
        resource = f"{self._endpoint}/{route}"
        if not hasattr(requests, verb.lower()):
            raise WebServiceClientError(f"unexpected verb: {verb} (while calling {resource})")
        dispatcher = getattr(requests, verb.lower())
        try:
            response = dispatcher(resource, json=serialize(payload))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise WebServiceClientError(f"error while sending request to {resource}: {e}")
        return orjson.loads(response.content)

    def get(self, route: str) -> Any:
        return self.send_request("get", route)

    def post(self, route: str, payload: Optional[Any] = None) -> Any:
        return self.send_request("post", route, payload)

    @property
    def healthy(self) -> bool:
        return core_schema.HealthResponse.parse_obj(self.get("healthy/")).healthy

    @classmethod
    def create(cls) -> Self:
        return cls(environment.get_web_service_endpoint(cls.service_name))


class CustomJsonProvider(DefaultJSONProvider):
    def dumps(self, obj: t.Any, **kwargs: t.Any) -> str:
        return orjson.dumps(
            obj,
            default=DefaultJSONProvider.default,
        ).decode()

    def loads(self, s: str | bytes, **kwargs: t.Any) -> t.Any:
        return orjson.loads(s)
