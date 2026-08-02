import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv import serializer
from finbot.apps.appwsrv.core import portfolios as appwsrv_portfolios
from finbot.apps.appwsrv.core.portfolio_valuation import estimate_portfolio_values
from finbot.apps.http_base import CurrentUserIdDep
from finbot.core.errors import InvalidUserInput, NotAllowedError
from finbot.core.jobs import JobPriority, JobSource
from finbot.core.schema import CurrencyCode
from finbot.model import Portfolio, PortfolioEntry, PortfolioSection, db, repository
from finbot.workflows.user_account_valuation import client as valuation_client
from finbot.workflows.user_account_valuation.schema import ValuationRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts/{user_account_id}/portfolios", tags=["Portfolios"])


def _valuation_ccy(user_account_id: int) -> CurrencyCode:
    return CurrencyCode(repository.get_user_account_settings(db.session, user_account_id).valuation_ccy)


async def _serialize(user_account_id: int, portfolio: Portfolio) -> appwsrv_schema.Portfolio:
    valuation_ccy = _valuation_ccy(user_account_id)
    estimates = await estimate_portfolio_values([portfolio], valuation_ccy)
    return serializer.serialize_portfolio(portfolio, estimates.get(portfolio.id), valuation_ccy)


@router.get("/", operation_id="get_portfolios")
async def get_portfolios(
    user_account_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.GetPortfoliosResponse:
    """Get portfolios"""
    if user_account_id != current_user_id:
        raise NotAllowedError()
    portfolios = [
        portfolio
        for portfolio in db.session.query(Portfolio)
        .filter_by(user_account_id=user_account_id)
        .order_by(Portfolio.id)
        .all()
        if not portfolio.linked_account.deleted
    ]
    valuation_ccy = _valuation_ccy(user_account_id)
    estimates = await estimate_portfolio_values(portfolios, valuation_ccy)
    return appwsrv_schema.GetPortfoliosResponse(
        portfolios=[
            serializer.serialize_portfolio_summary(portfolio, estimates.get(portfolio.id), valuation_ccy)
            for portfolio in portfolios
        ]
    )


@router.post("/", operation_id="create_portfolio")
async def create_portfolio(
    user_account_id: Annotated[int, Path()],
    json: appwsrv_schema.CreatePortfolioRequest,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.CreatePortfolioResponse:
    """Create portfolio"""
    if user_account_id != current_user_id:
        raise NotAllowedError()

    linked_account, portfolio = appwsrv_portfolios.create_portfolio_linked_account(
        session=db.session,
        user_account_id=user_account_id,
        name=json.name,
        colour=json.colour,
    )
    db.session.commit()
    db.session.refresh(portfolio)

    await valuation_client.kickoff_valuation(
        request=ValuationRequest(
            user_account_id=user_account_id,
            linked_accounts=[linked_account.id],
        ),
        priority=JobPriority.high,
        job_source=JobSource.app,
        ignore_errors=True,
    )
    return appwsrv_schema.CreatePortfolioResponse(portfolio=await _serialize(user_account_id, portfolio))


@router.get("/convert/preview/", operation_id="get_conversion_preview")
def get_conversion_preview(
    user_account_id: Annotated[int, Path()],
    linked_account_id: Annotated[int, Query()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.GetConversionPreviewResponse:
    """Show what an account would look like as a portfolio, without converting it"""
    if user_account_id != current_user_id:
        raise NotAllowedError()
    return serializer.serialize_conversion_preview(
        appwsrv_portfolios.plan_conversion(
            session=db.session,
            user_account_id=user_account_id,
            linked_account_id=linked_account_id,
        )
    )


@router.post("/convert/", operation_id="convert_linked_account_to_portfolio")
async def convert_linked_account_to_portfolio(
    user_account_id: Annotated[int, Path()],
    json: appwsrv_schema.ConvertLinkedAccountRequest,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.ConvertLinkedAccountResponse:
    """Turn an existing linked account into a Finbot managed portfolio"""
    if user_account_id != current_user_id:
        raise NotAllowedError()

    portfolio = appwsrv_portfolios.convert_linked_account(
        session=db.session,
        user_account_id=user_account_id,
        linked_account_id=json.linked_account_id,
    )
    db.session.commit()
    db.session.refresh(portfolio)

    await valuation_client.kickoff_valuation(
        request=ValuationRequest(
            user_account_id=user_account_id,
            linked_accounts=[portfolio.linked_account_id],
        ),
        priority=JobPriority.high,
        job_source=JobSource.app,
        ignore_errors=True,
    )
    return appwsrv_schema.ConvertLinkedAccountResponse(portfolio=await _serialize(user_account_id, portfolio))


@router.get("/{portfolio_id}/", operation_id="get_portfolio")
async def get_portfolio(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.GetPortfolioResponse:
    """Get portfolio"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    return appwsrv_schema.GetPortfolioResponse(portfolio=await _serialize(user_account_id, portfolio))


@router.put("/{portfolio_id}/", operation_id="update_portfolio")
async def update_portfolio(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    json: appwsrv_schema.UpdatePortfolioRequest,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.UpdatePortfolioResponse:
    """Update portfolio"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    linked_account = portfolio.linked_account
    if name := json.name:
        from finbot.model import repository

        if name != linked_account.account_name and repository.linked_account_exists(db.session, user_account_id, name):
            raise InvalidUserInput(f"A linked account with name '{name}' already exists")
        linked_account.account_name = name
    if colour := json.colour:
        linked_account.account_colour = colour
    db.session.commit()
    return appwsrv_schema.UpdatePortfolioResponse(portfolio=await _serialize(user_account_id, portfolio))


@router.delete("/{portfolio_id}/", operation_id="delete_portfolio")
async def delete_portfolio(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.DeletePortfolioResponse:
    """Delete portfolio"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    linked_account = portfolio.linked_account
    # Same soft delete as regular linked accounts: the name is mangled to keep the uniqueness
    # constraint satisfiable, and the valuation history is preserved.
    linked_account.account_name = f"DELETED {uuid.uuid4()} / {linked_account.account_name}"
    linked_account.deleted = True
    db.session.commit()

    await valuation_client.kickoff_valuation(
        request=ValuationRequest(user_account_id=user_account_id),
        priority=JobPriority.high,
        job_source=JobSource.app,
        ignore_errors=True,
    )
    return appwsrv_schema.DeletePortfolioResponse()


@router.post("/{portfolio_id}/snapshot/", operation_id="refresh_portfolio")
async def refresh_portfolio(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.RefreshPortfolioResponse:
    """Take a new snapshot of this portfolio"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    await valuation_client.kickoff_valuation(
        request=ValuationRequest(
            user_account_id=user_account_id,
            linked_accounts=[portfolio.linked_account_id],
        ),
        priority=JobPriority.high,
        job_source=JobSource.app,
        ignore_errors=True,
    )
    return appwsrv_schema.RefreshPortfolioResponse()


@router.post("/{portfolio_id}/sections/", operation_id="create_portfolio_section")
async def create_portfolio_section(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    json: appwsrv_schema.PortfolioSectionPayload,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.CreatePortfolioSectionResponse:
    """Create portfolio section"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    section = PortfolioSection(
        portfolio_id=portfolio.id,
        section_id=appwsrv_portfolios.make_section_id(
            json.name, {existing.section_id for existing in portfolio.sections}
        ),
        display_order=appwsrv_portfolios.next_display_order(portfolio.sections),
    )
    appwsrv_portfolios.apply_section_payload(section, json)
    db.session.add(section)
    db.session.commit()
    db.session.refresh(portfolio)
    return appwsrv_schema.CreatePortfolioSectionResponse(portfolio=await _serialize(user_account_id, portfolio))


@router.put("/{portfolio_id}/sections/{section_id}/", operation_id="update_portfolio_section")
async def update_portfolio_section(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    section_id: Annotated[int, Path()],
    json: appwsrv_schema.PortfolioSectionPayload,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.UpdatePortfolioSectionResponse:
    """Update portfolio section"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    section = appwsrv_portfolios.get_section(portfolio, section_id)
    appwsrv_portfolios.apply_section_payload(section, json)
    _drop_orphaned_custom_values(section)
    db.session.commit()
    db.session.refresh(portfolio)
    return appwsrv_schema.UpdatePortfolioSectionResponse(portfolio=await _serialize(user_account_id, portfolio))


@router.delete("/{portfolio_id}/sections/{section_id}/", operation_id="delete_portfolio_section")
async def delete_portfolio_section(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    section_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.DeletePortfolioSectionResponse:
    """Delete portfolio section"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    section = appwsrv_portfolios.get_section(portfolio, section_id)
    db.session.delete(section)  # type: ignore
    db.session.commit()
    db.session.refresh(portfolio)
    return appwsrv_schema.DeletePortfolioSectionResponse(portfolio=await _serialize(user_account_id, portfolio))


@router.post("/{portfolio_id}/sections/{section_id}/entries/", operation_id="create_portfolio_entry")
async def create_portfolio_entry(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    section_id: Annotated[int, Path()],
    json: appwsrv_schema.PortfolioEntryPayload,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.CreatePortfolioEntryResponse:
    """Create portfolio entry"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    section = appwsrv_portfolios.get_section(portfolio, section_id)
    entry = PortfolioEntry(
        portfolio_section_id=section.id,
        display_order=appwsrv_portfolios.next_display_order(section.entries),
    )
    await appwsrv_portfolios.apply_entry_payload(entry, json, section)
    db.session.add(entry)
    db.session.commit()
    db.session.refresh(portfolio)
    return appwsrv_schema.CreatePortfolioEntryResponse(portfolio=await _serialize(user_account_id, portfolio))


@router.put("/{portfolio_id}/entries/{entry_id}/", operation_id="update_portfolio_entry")
async def update_portfolio_entry(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    entry_id: Annotated[int, Path()],
    json: appwsrv_schema.PortfolioEntryPayload,
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.UpdatePortfolioEntryResponse:
    """Update portfolio entry"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    entry = appwsrv_portfolios.get_entry(portfolio, entry_id)
    await appwsrv_portfolios.apply_entry_payload(entry, json, entry.section)
    db.session.commit()
    db.session.refresh(portfolio)
    return appwsrv_schema.UpdatePortfolioEntryResponse(portfolio=await _serialize(user_account_id, portfolio))


@router.delete("/{portfolio_id}/entries/{entry_id}/", operation_id="delete_portfolio_entry")
async def delete_portfolio_entry(
    user_account_id: Annotated[int, Path()],
    portfolio_id: Annotated[int, Path()],
    entry_id: Annotated[int, Path()],
    current_user_id: CurrentUserIdDep,
) -> appwsrv_schema.DeletePortfolioEntryResponse:
    """Delete portfolio entry"""
    portfolio = _get_portfolio(user_account_id, current_user_id, portfolio_id)
    entry = appwsrv_portfolios.get_entry(portfolio, entry_id)
    db.session.delete(entry)  # type: ignore
    db.session.commit()
    db.session.refresh(portfolio)
    return appwsrv_schema.DeletePortfolioEntryResponse(portfolio=await _serialize(user_account_id, portfolio))


def _get_portfolio(user_account_id: int, current_user_id: int, portfolio_id: int) -> Portfolio:
    if user_account_id != current_user_id:
        raise NotAllowedError()
    return appwsrv_portfolios.get_portfolio(db.session, user_account_id, portfolio_id)


def _drop_orphaned_custom_values(section: PortfolioSection) -> None:
    """Removing a custom column removes the values entries were holding for it."""
    known_keys = {column["key"] for column in (section.custom_columns or [])}
    for entry in section.entries:
        if not entry.custom_values:
            continue
        kept = {key: value for key, value in entry.custom_values.items() if key in known_keys}
        if len(kept) != len(entry.custom_values):
            entry.custom_values = kept
