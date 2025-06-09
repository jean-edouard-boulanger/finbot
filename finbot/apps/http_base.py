import logging
import traceback
from http import HTTPStatus
from typing import Annotated, Any, Awaitable, Callable
from uuid import uuid4

import orjson
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from finbot.core import jwt
from finbot.core.errors import AuthError, InvalidOperation, InvalidUserInput, NotAllowedError, ResourceNotFoundError
from finbot.core.jwt import JwtTokenPayload
from finbot.core.schema import ApplicationErrorResponse, GenericError
from finbot.core.utils import some
from finbot.model import ScopedSession, UserAccount, db

security = HTTPBearer()


logger = logging.getLogger(__name__)


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return orjson.dumps(content)


def setup_app(app: FastAPI) -> FastAPI:
    @app.middleware("http")
    async def manage_db_session(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        with ScopedSession():
            response = await call_next(request)
        return response

    @app.exception_handler(ResourceNotFoundError)
    def resource_not_found_error_handler(request: Request, exc: ResourceNotFoundError) -> Response:
        return ORJSONResponse(
            status_code=HTTPStatus.NOT_FOUND, content=GenericError(error=str(exc), code=exc.error_code).model_dump()
        )

    @app.exception_handler(AuthError)
    def auth_error_exception_handler(request: Request, exc: AuthError) -> Response:
        return ORJSONResponse(
            status_code=HTTPStatus.UNAUTHORIZED,
            content=GenericError(
                error="User is not authorized to perform this operation", code=exc.error_code
            ).model_dump(),
        )

    @app.exception_handler(NotAllowedError)
    def not_allowed_exception_handler(request: Request, exc: NotAllowedError) -> Response:
        return ORJSONResponse(
            status_code=HTTPStatus.FORBIDDEN,
            content=GenericError(
                error="User is not authorized to perform this operation", code=exc.error_code
            ).model_dump(),
        )

    @app.exception_handler(InvalidUserInput)
    @app.exception_handler(InvalidOperation)
    def invalid_operation_exception_handler(request: Request, exc: InvalidOperation | InvalidUserInput) -> Response:
        return ORJSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content=GenericError(error=f"{exc}", code=exc.error_code).model_dump(),
        )

    @app.exception_handler(Exception)
    def generic_exception_handler(request: Request, exc: Exception) -> Response:
        error_handle = str(uuid4())
        logger.error(f"error while processing request: {exc} (handle: {error_handle})\n{traceback.format_exc()}")
        return ORJSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content=ApplicationErrorResponse.from_exception(exc).model_dump(),
        )

    # TODO: only fine for development use cases.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    return app


def get_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> JwtTokenPayload:
    token = credentials.credentials
    return jwt.verify_token(token, "access")


JwtTokenDep = Annotated[jwt.JwtTokenPayload, Depends(get_jwt_token)]


def get_current_user_id(jwt_token: JwtTokenDep) -> int:
    return int(jwt_token.sub)


CurrentUserIdDep = Annotated[int, Depends(get_current_user_id)]


def get_current_user(current_user_id: CurrentUserIdDep) -> UserAccount:
    return some(db.session.query(UserAccount).get(current_user_id))


CurrentUserDep = Annotated[UserAccount, Depends(get_current_user)]
