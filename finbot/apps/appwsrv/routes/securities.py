import logging
from typing import Annotated

from fastapi import APIRouter, Query

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.http_base import CurrentUserIdDep
from finbot.core.errors import InvalidUserInput
from finbot.core.securities_market import SecuritiesMarket, SecuritiesMarketError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/securities", tags=["Securities"])


@router.get("/resolve/", operation_id="resolve_security")
async def resolve_security(
    symbol: Annotated[str, Query(min_length=1, max_length=32)],
    _: CurrentUserIdDep,
) -> appwsrv_schema.ResolveSecurityResponse:
    """Resolve a security by its Yahoo Finance symbol"""
    try:
        quote = await SecuritiesMarket().async_get_quote(symbol.strip(), with_name=True)
    except SecuritiesMarketError as e:
        raise InvalidUserInput(str(e))
    return appwsrv_schema.ResolveSecurityResponse(quote=serializer.serialize_security_quote(quote))
