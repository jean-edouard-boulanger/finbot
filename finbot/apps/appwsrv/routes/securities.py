import logging
from typing import Annotated

from fastapi import APIRouter, Query

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.http_base import CurrentUserIdDep
from finbot.core.errors import InvalidUserInput
from finbot.core.securities_market import (
    DEFAULT_SEARCH_RESULTS,
    MAX_SEARCH_RESULTS,
    SecuritiesMarket,
    SecuritiesMarketError,
    SecurityKind,
)

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


@router.get("/search/", operation_id="search_securities")
async def search_securities(
    query: Annotated[str, Query(min_length=2, max_length=64, alias="q")],
    _: CurrentUserIdDep,
    kind: SecurityKind | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_SEARCH_RESULTS)] = DEFAULT_SEARCH_RESULTS,
) -> appwsrv_schema.SearchSecuritiesResponse:
    """Search Yahoo Finance securities by symbol or name"""
    try:
        results = await SecuritiesMarket().async_search_cached(query.strip(), kind=kind, limit=limit)
    except SecuritiesMarketError:
        # Suggestions are a convenience: a symbol can still be typed in by hand, so an unreachable
        # Yahoo Finance is reported to the caller rather than failing the request.
        logger.warning("securities search failed", exc_info=True)
        return appwsrv_schema.SearchSecuritiesResponse(results=[], provider_available=False)
    return appwsrv_schema.SearchSecuritiesResponse(
        results=[serializer.serialize_security_search_result(result) for result in results],
        provider_available=True,
    )
