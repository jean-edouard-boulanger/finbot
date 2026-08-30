import logging
from typing import Any, Literal, TypeAlias, cast

from finbot import model
from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv.core import portfolios as portfolios_core
from finbot.apps.appwsrv.core.portfolio_valuation import PortfolioValuationEstimate
from finbot.core import schema as core_schema
from finbot.core import securities_market
from finbot.core.email_delivery import DeliverySettings
from finbot.core.serialization import reinterpret_as_pydantic
from finbot.model import repository
from finbot.providers import schema as providers_schema

logger = logging.getLogger(__name__)


def serialize_user_account(
    user_account: model.UserAccount,
) -> appwsrv_schema.UserAccount:
    return appwsrv_schema.UserAccount(
        id=user_account.id,
        email=user_account.email,
        full_name=user_account.full_name,
        mobile_phone_number=user_account.mobile_phone_number,
        is_demo=user_account.is_demo,
        created_at=user_account.created_at,
        updated_at=user_account.updated_at,
    )


def serialize_user_account_profile(
    user_account: model.UserAccount,
) -> appwsrv_schema.UserAccountProfile:
    return appwsrv_schema.UserAccountProfile(
        email=user_account.email,
        full_name=user_account.full_name,
        mobile_phone_number=user_account.mobile_phone_number,
    )


def serialize_user_account_settings(
    settings: model.UserAccountSettings,
) -> appwsrv_schema.UserAccountSettings:
    return appwsrv_schema.UserAccountSettings(
        valuation_ccy=settings.valuation_ccy,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


def serialize_linked_account_status(
    linked_account_status: repository.LinkedAccountStatus | None,
) -> appwsrv_schema.LinkedAccountStatus | None:
    return appwsrv_schema.LinkedAccountStatus.model_validate(linked_account_status) if linked_account_status else None


def serialize_provider(provider: model.Provider) -> appwsrv_schema.Provider:
    return appwsrv_schema.Provider(
        id=provider.id,
        description=provider.description,
        website_url=provider.website_url,
        credentials_schema=provider.credentials_schema,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


def serialize_merchant(merchant: model.Merchant) -> appwsrv_schema.MerchantEntry:
    return appwsrv_schema.MerchantEntry(
        id=merchant.id,
        name=merchant.name,
        description=merchant.description,
        category=merchant.category,
        website_url=merchant.website_url,
        created_at=merchant.created_at,
        updated_at=merchant.updated_at,
    )


def serialize_linked_account(
    linked_account: model.LinkedAccount,
    linked_account_status: repository.LinkedAccountStatus | None,
    credentials: Any,
) -> appwsrv_schema.LinkedAccount:
    return appwsrv_schema.LinkedAccount(
        id=linked_account.id,
        user_account_id=linked_account.user_account_id,
        account_name=linked_account.account_name,
        account_colour=linked_account.account_colour,
        deleted=linked_account.deleted,
        frozen=linked_account.frozen,
        provider_id=linked_account.provider.id,
        provider=serialize_provider(linked_account.provider),
        portfolio_id=(linked_account.portfolio.id if linked_account.portfolio else None),
        status=serialize_linked_account_status(linked_account_status),
        credentials=credentials,
        created_at=linked_account.created_at,
        updated_at=linked_account.updated_at,
    )


def serialize_valuation_change(
    change: model.ValuationChangeEntry,
) -> core_schema.ValuationChange:
    return reinterpret_as_pydantic(core_schema.ValuationChange, change)


def serialize_email_delivery_settings(
    settings: DeliverySettings | None,
) -> appwsrv_schema.EmailDeliverySettings | None:
    return (
        appwsrv_schema.EmailDeliverySettings(
            subject_prefix=settings.subject_prefix,
            sender_name=settings.sender_name,
            provider_id=settings.provider_id,
            provider_settings=settings.provider_settings,
        )
        if settings
        else None
    )


def _portfolio_entry_unit_price(entry: model.PortfolioEntry) -> float | None:
    if entry.price_source == model.PortfolioEntryPriceSource.Manual:
        return float(entry.manual_unit_price) if entry.manual_unit_price is not None else None
    return float(entry.last_resolved_unit_price) if entry.last_resolved_unit_price is not None else None


def serialize_portfolio_entry(
    entry: model.PortfolioEntry,
    estimate: PortfolioValuationEstimate | None,
) -> appwsrv_schema.PortfolioEntry:
    unit_price = _portfolio_entry_unit_price(entry)
    units = float(entry.units)
    return appwsrv_schema.PortfolioEntry(
        id=entry.id,
        item_type=("liability" if entry.item_type == model.SubAccountItemType.Liability else "asset"),
        name=entry.name,
        asset_class=(providers_schema.AssetClass(entry.asset_class) if entry.asset_class else None),
        asset_type=(providers_schema.AssetType(entry.asset_type) if entry.asset_type else None),
        liability_type=entry.liability_type,
        currency=core_schema.CurrencyCode(entry.currency),
        units=units,
        price_source=("proxy" if entry.price_source == model.PortfolioEntryPriceSource.Proxy else "manual"),
        unit_price=unit_price,
        manual_unit_price=(float(entry.manual_unit_price) if entry.manual_unit_price is not None else None),
        manual_price_updated_at=entry.manual_price_updated_at,
        proxy_symbol=entry.proxy_symbol,
        proxy_name=entry.proxy_name,
        last_resolved_unit_price=(
            float(entry.last_resolved_unit_price) if entry.last_resolved_unit_price is not None else None
        ),
        last_resolved_price_at=entry.last_resolved_price_at,
        isin_code=entry.isin_code,
        custom_values=entry.custom_values or {},
        value=(units * unit_price if unit_price is not None else None),
        estimated_value=(estimate.by_entry.get(entry.id) if estimate else None),
        display_order=entry.display_order,
    )


def serialize_portfolio_section(
    section: model.PortfolioSection,
    estimate: PortfolioValuationEstimate | None,
) -> appwsrv_schema.PortfolioSection:
    return appwsrv_schema.PortfolioSection(
        id=section.id,
        section_id=section.section_id,
        name=section.name,
        currency=core_schema.CurrencyCode(section.currency),
        account_type=providers_schema.AccountType(section.account_type),
        account_sub_type=section.account_sub_type,
        custom_columns=[
            appwsrv_schema.PortfolioCustomColumn.model_validate(column) for column in (section.custom_columns or [])
        ],
        display_order=section.display_order,
        estimated_value=(estimate.by_section.get(section.id) if estimate else None),
        entries=[serialize_portfolio_entry(entry, estimate) for entry in section.entries],
    )


def serialize_portfolio(
    portfolio: model.Portfolio,
    estimate: PortfolioValuationEstimate | None,
    valuation_ccy: str,
) -> appwsrv_schema.Portfolio:
    linked_account = portfolio.linked_account
    return appwsrv_schema.Portfolio(
        id=portfolio.id,
        linked_account_id=portfolio.linked_account_id,
        name=linked_account.account_name,
        colour=linked_account.account_colour,
        frozen=linked_account.frozen,
        estimated_value=(estimate.total if estimate else None),
        valuation_ccy=valuation_ccy,
        sections=[serialize_portfolio_section(section, estimate) for section in portfolio.sections],
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


def serialize_portfolio_summary(
    portfolio: model.Portfolio,
    estimate: PortfolioValuationEstimate | None,
    valuation_ccy: str,
) -> appwsrv_schema.PortfolioSummary:
    linked_account = portfolio.linked_account
    return appwsrv_schema.PortfolioSummary(
        id=portfolio.id,
        linked_account_id=portfolio.linked_account_id,
        name=linked_account.account_name,
        colour=linked_account.account_colour,
        frozen=linked_account.frozen,
        sections_count=len(portfolio.sections),
        entries_count=sum(len(section.entries) for section in portfolio.sections),
        estimated_value=(estimate.total if estimate else None),
        valuation_ccy=valuation_ccy,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


def serialize_security_quote(quote: securities_market.SecurityQuote) -> appwsrv_schema.SecurityQuote:
    return appwsrv_schema.SecurityQuote(
        symbol=quote.symbol,
        name=quote.name,
        currency=quote.currency,
        price=quote.price,
        as_of=quote.as_of,
    )


def serialize_security_search_result(
    result: securities_market.SecuritySearchResult,
) -> appwsrv_schema.SecuritySearchResult:
    return appwsrv_schema.SecuritySearchResult(
        symbol=result.symbol,
        name=result.name,
        kind=result.kind,
        exchange=result.exchange,
    )


def serialize_conversion_preview(
    plan: portfolios_core.ConversionPlan,
) -> appwsrv_schema.GetConversionPreviewResponse:
    return appwsrv_schema.GetConversionPreviewResponse(
        account_name=plan.account_name,
        valued_at=plan.valued_at,
        holdings_count=plan.holdings_count,
        sections=[
            appwsrv_schema.ConversionPreviewSection(
                name=section.name,
                currency=core_schema.CurrencyCode(section.currency),
                detail_columns=section.detail_columns,
                holdings=[
                    appwsrv_schema.ConversionPreviewHolding(
                        name=holding.name,
                        value=holding.value,
                        currency=core_schema.CurrencyCode(holding.currency),
                        is_liability=holding.item_type == model.SubAccountItemType.Liability,
                    )
                    for holding in section.holdings
                ],
            )
            for section in plan.sections
        ],
    )


NotificationSeverity: TypeAlias = Literal["info", "warning", "error", "success"]
NotificationStatus: TypeAlias = Literal["active", "resolved"]

_NOTIFICATION_SEVERITIES: frozenset[str] = frozenset(("info", "warning", "error", "success"))
_NOTIFICATION_STATUSES: frozenset[str] = frozenset(("active", "resolved"))


def _notification_severity(value: str) -> NotificationSeverity:
    """Severity is stored as a plain string, so a value written by older code cannot break the whole panel."""
    if value in _NOTIFICATION_SEVERITIES:
        return cast(NotificationSeverity, value)
    logger.warning(f"unknown notification severity '{value}', falling back to 'info'")
    return "info"


def _notification_status(value: str) -> NotificationStatus:
    if value in _NOTIFICATION_STATUSES:
        return cast(NotificationStatus, value)
    logger.warning(f"unknown notification status '{value}', falling back to 'active'")
    return "active"


def serialize_notification(notification: model.Notification) -> appwsrv_schema.Notification:
    return appwsrv_schema.Notification(
        id=notification.id,
        notification_type=notification.notification_type,
        severity=_notification_severity(notification.severity),
        status=_notification_status(notification.status),
        title=notification.title,
        body=notification.body,
        payload=notification.payload,
        occurrences=notification.occurrences,
        created_at=notification.created_at,
        last_seen_at=notification.last_seen_at,
        resolved_at=notification.resolved_at,
        read_at=notification.read_at,
    )
