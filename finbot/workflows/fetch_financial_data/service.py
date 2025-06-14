import logging
from typing import Any, cast

from finbot.core.environment import get_secret_key
from finbot.core.schema import ApplicationErrorData, CurrencyCode
from finbot.core.secure import fernet_decrypt_json
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationError
from finbot.providers.factory import get_provider
from finbot.workflows.fetch_financial_data import schema

logger = logging.getLogger(__name__)


async def accounts_handler(provider_api: ProviderBase) -> schema.LineItemResults:
    return schema.AccountsResults(results=await provider_api.get_accounts())


async def assets_handler(provider_api: ProviderBase) -> schema.LineItemResults:
    return schema.AssetsResults(results=(await provider_api.get_assets()).accounts)


async def liabilities_handler(provider_api: ProviderBase) -> schema.LineItemResults:
    return schema.LiabilitiesResults(results=(await provider_api.get_liabilities()).accounts)


async def item_handler(
    item_type: schema.LineItem,
    provider_api: ProviderBase,
) -> schema.LineItemResults:
    handler = {
        schema.LineItem.Accounts: accounts_handler,
        schema.LineItem.Assets: assets_handler,
        schema.LineItem.Liabilities: liabilities_handler,
    }.get(item_type)
    try:
        if not handler:
            raise ValueError(f"unknown line item: '{item_type}'")
        logger.debug(f"handling '{item_type}' line item")
        return await handler(provider_api)
    except Exception as e:
        logger.exception(f"error while handling '{item_type}'")
        return schema.LineItemError(
            line_item=item_type,
            error=ApplicationErrorData.from_exception(e),
        )


async def get_financial_data_impl(
    provider_type: type[ProviderBase],
    authentication_payload: dict[str, Any],
    line_items: list[schema.LineItem],
    user_account_currency: CurrencyCode,
) -> schema.GetFinancialDataResponse:
    async with provider_type.create(authentication_payload, user_account_currency) as provider_api:
        await provider_api.initialize()
        return schema.GetFinancialDataResponse(
            financial_data=[await item_handler(line_item, provider_api) for line_item in set(line_items)]
        )


class FinancialDataFetcherService:
    @classmethod
    async def get_financial_data(cls, request: schema.GetFinancialDataRequest) -> schema.GetFinancialDataResponse:
        try:
            provider_type = get_provider(request.provider_id)
            return await get_financial_data_impl(
                provider_type=provider_type,
                authentication_payload=cast(
                    dict[str, Any],
                    fernet_decrypt_json(request.encrypted_credentials, get_secret_key()),
                ),
                line_items=request.items,
                user_account_currency=request.user_account_currency,
            )
        except Exception as e:
            return schema.GetFinancialDataResponse(
                financial_data=[],
                error=ApplicationErrorData.from_exception(e),
            )

    @classmethod
    async def validate_credentials(
        cls,
        request: schema.ValidateCredentialsRequest,
    ) -> schema.ValidateCredentialsResponse:
        provider_type = get_provider(request.provider_id)
        authentication_payload = cast(
            dict[str, Any], fernet_decrypt_json(request.encrypted_credentials, get_secret_key())
        )
        async with provider_type.create(authentication_payload, request.user_account_currency) as provider:
            try:
                await provider.initialize()
                return schema.ValidateCredentialsResponse(valid=True)
            except AuthenticationError as e:
                return schema.ValidateCredentialsResponse(valid=False, error_message=str(e))
