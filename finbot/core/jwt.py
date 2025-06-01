from datetime import timedelta
from typing import Any, Literal, Optional

from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict

from finbot.core.environment import get_jwt_secret_key
from finbot.core.errors import InvalidJwtError
from finbot.core.utils import now_utc, strict_cast

ALGORITHM = "HS256"


class JwtTokenPayload(BaseModel):
    sub: str
    exp: int
    type: Literal["access", "refresh"]

    model_config = ConfigDict(extra="ignore")


def create_token(
    identity: str,
    type_: Literal["access", "refresh"],
    expires_delta: Optional[timedelta],
) -> str:
    to_encode: dict[str, Any] = {"sub": identity}
    if expires_delta:
        expire = now_utc() + expires_delta
    else:
        expire = now_utc() + timedelta(minutes=15)

    to_encode.update({"exp": expire, "type": type_})
    return strict_cast(str, jwt.encode(to_encode, get_jwt_secret_key(), algorithm=ALGORITHM))


def create_refresh_token(
    identity: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    return create_token(
        identity=identity,
        type_="refresh",
        expires_delta=expires_delta,
    )


def create_access_token(
    identity: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    return create_token(
        identity=identity,
        type_="access",
        expires_delta=expires_delta,
    )


def verify_token(
    token: str,
    token_type: str = "access",
) -> JwtTokenPayload:
    try:
        payload = jwt.decode(token, get_jwt_secret_key(), algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        exp: int = payload.get("exp")
        token_type_claim: str = payload.get("type")

        if user_id is None or token_type_claim != token_type:
            raise InvalidJwtError()

        if exp and now_utc().timestamp() > exp:
            raise InvalidJwtError()

        return JwtTokenPayload(**payload)
    except JWTError:
        raise InvalidJwtError()
