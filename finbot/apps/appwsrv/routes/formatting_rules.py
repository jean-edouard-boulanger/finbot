from fastapi import APIRouter

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv.core.formatting_rules import ACCOUNTS_PALETTE
from finbot.apps.http_base import CurrentUserIdDep

router = APIRouter(prefix="/formatting_rules", tags=["Formatting rules"])


@router.get("/accounts/", operation_id="get_accounts_formatting_rules")
def get_accounts_formatting_rules(
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetAccountsFormattingRulesResponse:
    """Get accounts formatting rules"""
    return appwsrv_schema.GetAccountsFormattingRulesResponse(
        colour_palette=ACCOUNTS_PALETTE,
    )
