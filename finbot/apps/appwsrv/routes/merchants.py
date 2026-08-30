from fastapi import APIRouter

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.http_base import CurrentUserIdDep
from finbot.model import Merchant, db

router = APIRouter(
    prefix="/merchants",
    tags=["Merchants"],
)


@router.get(
    "/",
    operation_id="get_merchants",
)
def get_merchants(
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetMerchantsResponse:
    """Get all auto-extracted merchants"""
    return appwsrv_schema.GetMerchantsResponse(
        merchants=[
            serializer.serialize_merchant(merchant)
            for merchant in db.session.query(Merchant).order_by(Merchant.name).all()
        ]
    )
