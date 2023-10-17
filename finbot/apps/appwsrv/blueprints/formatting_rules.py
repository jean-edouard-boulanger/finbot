from flask import Blueprint

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv.blueprints.base import API_URL_PREFIX
from finbot.apps.appwsrv.core.formatting_rules import ACCOUNTS_PALETTE
from finbot.core.web_service import jwt_required, service_endpoint, validate

formatting_rules_api = Blueprint(
    name="formatting_rules_api",
    import_name=__name__,
    url_prefix=f"{API_URL_PREFIX}/formatting_rules",
)


@formatting_rules_api.route("/accounts/", methods=["GET"])
@jwt_required()
@service_endpoint()
@validate()
def get_accounts_formatting_rules() -> (
    appwsrv_schema.GetAccountsFormattingRulesResponse
):
    return appwsrv_schema.GetAccountsFormattingRulesResponse(
        colour_palette=ACCOUNTS_PALETTE
    )
