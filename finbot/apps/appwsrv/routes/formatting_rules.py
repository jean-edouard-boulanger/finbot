from fastapi import APIRouter

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv.core.formatting_rules import (
    ACCOUNTS_PALETTE,
    get_asset_classes_formatting_rules,
    get_asset_types_formatting_rules,
)
from finbot.apps.http_base import CurrentUserIdDep
from finbot.providers.schema import VALID_ACCOUNT_SUB_TYPES

router = APIRouter(prefix="/formatting_rules", tags=["Formatting rules"])


@router.get("/assets/", operation_id="get_assets_formatting_rules")
def get_assets_formatting_rules(
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetAssetsFormattingRulesResponse:
    """Get the display name and colour to use for each asset class and type"""
    return appwsrv_schema.GetAssetsFormattingRulesResponse(
        asset_classes=list(get_asset_classes_formatting_rules().values()),
        asset_types=list(get_asset_types_formatting_rules().values()),
    )


@router.get("/account_sub_types/", operation_id="get_account_sub_types")
def get_account_sub_types(
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetAccountSubTypesResponse:
    """Get the account sub types valid for each account type"""
    return appwsrv_schema.GetAccountSubTypesResponse(
        account_sub_types=[
            appwsrv_schema.AccountSubTypes(
                account_type=account_type,
                sub_types=[sub_type for sub_type in sub_types if sub_type is not None],
            )
            for account_type, sub_types in VALID_ACCOUNT_SUB_TYPES.items()
        ]
    )


@router.get("/accounts/", operation_id="get_accounts_formatting_rules")
def get_accounts_formatting_rules(
    _: CurrentUserIdDep,
) -> appwsrv_schema.GetAccountsFormattingRulesResponse:
    """Get accounts formatting rules"""
    return appwsrv_schema.GetAccountsFormattingRulesResponse(
        colour_palette=ACCOUNTS_PALETTE,
    )
