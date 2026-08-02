import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy.exc import IntegrityError

from finbot.apps.appwsrv import schema as appwsrv_schema
from finbot.apps.appwsrv.core import providers as appwsrv_providers
from finbot.core import environment, secure
from finbot.core.errors import InvalidOperation, InvalidUserInput, ResourceNotFoundError
from finbot.core.securities_market import SecuritiesMarket
from finbot.core.utils import now_utc, some
from finbot.model import (
    LinkedAccount,
    LinkedAccountSnapshotEntry,
    Portfolio,
    PortfolioEntry,
    PortfolioEntryPriceSource,
    PortfolioSection,
    SessionType,
    SubAccountItemSnapshotEntry,
    SubAccountItemType,
    SubAccountSnapshotEntry,
    UserAccountSnapshot,
    repository,
)

logger = logging.getLogger(__name__)

_SECTION_ID_MAX_LENGTH = 64
CUSTOM_COLUMN_KEY_MAX_LENGTH = 64


def make_section_id(name: str, taken: set[str]) -> str:
    """Build a stable, human-readable sub-account identifier for a new section.

    Valuation history is keyed on this identifier, so it is generated once and never changed
    afterwards (renaming a section only changes its display name).
    """
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")[:48] or "section"
    candidate = slug
    while candidate in taken:
        candidate = f"{slug}-{uuid.uuid4().hex[:6]}"[:_SECTION_ID_MAX_LENGTH]
    return candidate


def get_portfolio(session: SessionType, user_account_id: int, portfolio_id: int) -> Portfolio:
    portfolio = session.query(Portfolio).filter_by(id=portfolio_id, user_account_id=user_account_id).one_or_none()
    if portfolio is None:
        raise ResourceNotFoundError(f"Portfolio {portfolio_id} does not exist")
    return portfolio


def get_section(portfolio: Portfolio, section_id: int) -> PortfolioSection:
    for section in portfolio.sections:
        if section.id == section_id:
            return section
    raise ResourceNotFoundError(f"Section {section_id} does not exist in this portfolio")


def get_entry(portfolio: Portfolio, entry_id: int) -> PortfolioEntry:
    for section in portfolio.sections:
        for entry in section.entries:
            if entry.id == entry_id:
                return entry
    raise ResourceNotFoundError(f"Entry {entry_id} does not exist in this portfolio")


def create_portfolio_linked_account(
    session: SessionType,
    user_account_id: int,
    name: str,
    colour: str,
) -> tuple[LinkedAccount, Portfolio]:
    """Create a portfolio along with the linked account that exposes it to the valuation pipeline.

    The linked account credentials reference the portfolio identifier, which is only known once the
    portfolio row has been flushed, hence the two-step commit.
    """
    if repository.linked_account_exists(session, user_account_id, name):
        raise InvalidUserInput(f"A linked account with name '{name}' already exists")

    linked_account = LinkedAccount(
        user_account_id=user_account_id,
        provider_id=appwsrv_providers.FINBOT_PORTFOLIO_PROVIDER_ID,
        account_name=name,
        account_colour=colour,
        deleted=False,
        frozen=False,
    )
    session.add(linked_account)
    session.flush()

    portfolio = Portfolio(user_account_id=user_account_id, linked_account_id=linked_account.id)
    session.add(portfolio)
    session.flush()

    linked_account.encrypted_credentials = secure.fernet_encrypt_json(
        {"portfolio_id": portfolio.id},
        environment.get_secret_key(),
    ).decode()
    session.flush()
    return linked_account, portfolio


def apply_section_payload(
    section: PortfolioSection,
    payload: appwsrv_schema.PortfolioSectionPayload,
) -> None:
    section.name = payload.name
    section.currency = payload.currency
    section.account_type = payload.account_type.value
    section.account_sub_type = payload.account_sub_type
    section.custom_columns = [column.model_dump(mode="json") for column in payload.custom_columns]


async def apply_entry_payload(
    entry: PortfolioEntry,
    payload: appwsrv_schema.PortfolioEntryPayload,
    section: PortfolioSection,
) -> None:
    _validate_custom_values(payload.custom_values, section)
    previous_manual_price = entry.manual_unit_price
    entry.item_type = SubAccountItemType.Liability if payload.item_type == "liability" else SubAccountItemType.Asset
    entry.name = payload.name
    entry.asset_class = payload.asset_class.value if payload.asset_class else None
    entry.asset_type = payload.asset_type.value if payload.asset_type else None
    entry.liability_type = payload.liability_type
    entry.units = _as_decimal(payload.units)
    entry.price_source = (
        PortfolioEntryPriceSource.Proxy if payload.price_source == "proxy" else PortfolioEntryPriceSource.Manual
    )
    entry.manual_unit_price = _as_optional_decimal(payload.manual_unit_price)
    entry.isin_code = payload.isin_code
    entry.custom_values = payload.custom_values

    if payload.price_source == "proxy":
        symbol_changed = entry.proxy_symbol != payload.proxy_symbol
        entry.proxy_symbol = payload.proxy_symbol
        entry.currency = payload.currency or entry.currency or section.currency
        if symbol_changed:
            # The previously resolved price now belongs to a different security. Resolve the new one
            # straight away so the entry shows a value without waiting for the next snapshot.
            entry.last_resolved_unit_price = None
            entry.last_resolved_price_at = None
            await _resolve_proxy_price(entry)
    else:
        entry.proxy_symbol = None
        entry.last_resolved_unit_price = None
        entry.last_resolved_price_at = None
        entry.currency = payload.currency or section.currency

    if _manual_price_changed(previous_manual_price, payload.manual_unit_price):
        entry.manual_price_updated_at = now_utc()


async def _resolve_proxy_price(entry: PortfolioEntry) -> None:
    """Best effort resolution of an entry's proxy security.

    A failure here is not fatal: the entry is still valid, and the snapshot will try again.
    """
    try:
        quote = await SecuritiesMarket().async_get_quote_cached(some(entry.proxy_symbol))
    except Exception:
        logger.warning(f"could not resolve proxy security '{entry.proxy_symbol}'", exc_info=True)
        return
    entry.last_resolved_unit_price = _as_decimal(quote.price)
    entry.last_resolved_price_at = quote.as_of
    entry.currency = quote.currency


def _as_decimal(value: float) -> Decimal:
    return Decimal(str(value))


def _as_optional_decimal(value: float | None) -> Decimal | None:
    return _as_decimal(value) if value is not None else None


def _manual_price_changed(previous: Any, current: float | None) -> bool:
    if current is None:
        return False
    if previous is None:
        return True
    return float(previous) != float(current)


def _validate_custom_values(
    custom_values: dict[str, str],
    section: PortfolioSection,
) -> None:
    known_keys = {column["key"] for column in (section.custom_columns or [])}
    unknown_keys = set(custom_values) - known_keys
    if unknown_keys:
        raise InvalidUserInput(
            f"Section '{section.name}' has no custom column named {', '.join(sorted(unknown_keys))}",
        )


def next_display_order(items: list[Any]) -> int:
    return max((item.display_order for item in items), default=-1) + 1


@dataclass(frozen=True)
class PlannedHolding:
    name: str
    units: float
    unit_price: float
    currency: str
    item_type: SubAccountItemType
    asset_class: str | None
    asset_type: str | None
    isin_code: str | None
    details: dict[str, str]

    @property
    def value(self) -> float:
        return self.units * self.unit_price


@dataclass(frozen=True)
class PlannedSection:
    section_id: str
    name: str
    currency: str
    account_type: str
    account_sub_type: str | None
    holdings: list[PlannedHolding]

    @property
    def detail_columns(self) -> list[str]:
        seen: dict[str, None] = {}
        for holding in self.holdings:
            for key in holding.details:
                seen.setdefault(key, None)
        return list(seen)


@dataclass(frozen=True)
class ConversionPlan:
    """Exactly what converting an account would produce, without producing it."""

    account_name: str
    valued_at: datetime | None
    sections: list[PlannedSection]

    @property
    def holdings_count(self) -> int:
        return sum(len(section.holdings) for section in self.sections)


def plan_conversion(
    session: SessionType,
    user_account_id: int,
    linked_account_id: int,
) -> ConversionPlan:
    """Work out the portfolio an account would become.

    Both the preview and the conversion itself read from here, so what is shown is what is built.
    """
    linked_account = repository.get_linked_account(
        session=session,
        user_account_id=user_account_id,
        linked_account_id=linked_account_id,
    )
    if appwsrv_providers.is_managed_provider(linked_account.provider_id):
        raise InvalidUserInput(f"'{linked_account.account_name}' is already a Finbot portfolio")

    snapshot_entry = _find_last_successful_snapshot_entry(session, linked_account_id)
    if snapshot_entry is None:
        raise InvalidUserInput(
            f"Finbot has never managed to read '{linked_account.account_name}', so there is nothing to convert yet"
        )
    snapshot = session.query(UserAccountSnapshot).filter_by(id=snapshot_entry.snapshot_id).one()

    taken_section_ids: set[str] = set()
    sections: list[PlannedSection] = []
    # The ORM relationships are untyped, so their collection nature has to be spelled out here.
    sub_account_entries = cast(list[SubAccountSnapshotEntry], snapshot_entry.sub_accounts_entries)
    for sub_account_entry in sub_account_entries:
        section_id = sub_account_entry.sub_account_id[:_SECTION_ID_MAX_LENGTH]
        if section_id in taken_section_ids:
            section_id = make_section_id(sub_account_entry.sub_account_description, taken_section_ids)
        taken_section_ids.add(section_id)

        holdings: list[PlannedHolding] = []
        item_entries = cast(list[SubAccountItemSnapshotEntry], sub_account_entry.items_entries)
        for item_entry in item_entries:
            units, unit_price = _split_units_and_price(item_entry)
            holdings.append(
                PlannedHolding(
                    name=item_entry.name,
                    units=units,
                    unit_price=unit_price,
                    currency=item_entry.currency or sub_account_entry.sub_account_ccy,
                    item_type=item_entry.item_type,
                    asset_class=item_entry.asset_class,
                    asset_type=item_entry.asset_type,
                    isin_code=item_entry.isin_code,
                    # Keys become custom column keys, which the API caps in length: truncate here
                    # so a conversion can never produce a portfolio that fails to serialize.
                    details={
                        str(key)[:CUSTOM_COLUMN_KEY_MAX_LENGTH]: str(value)
                        for key, value in (item_entry.provider_specific_data or {}).items()
                        if value is not None
                    },
                )
            )
        sections.append(
            PlannedSection(
                section_id=section_id,
                name=sub_account_entry.sub_account_description,
                currency=sub_account_entry.sub_account_ccy,
                account_type=sub_account_entry.sub_account_type,
                account_sub_type=sub_account_entry.sub_account_sub_type,
                holdings=holdings,
            )
        )
    return ConversionPlan(
        account_name=linked_account.account_name,
        valued_at=snapshot.effective_at,
        sections=sections,
    )


def convert_linked_account(
    session: SessionType,
    user_account_id: int,
    linked_account_id: int,
) -> Portfolio:
    """Turn an existing linked account into a Finbot managed portfolio, in place.

    The account keeps its identity: same id, same name, same valuation history, and the same single
    place in the user's net worth. Seeding a second account and retiring the first would double
    count, because a frozen account still contributes its last successful snapshot to every
    valuation that follows.
    """
    plan = plan_conversion(session, user_account_id, linked_account_id)
    linked_account = repository.get_linked_account(
        session=session,
        user_account_id=user_account_id,
        linked_account_id=linked_account_id,
    )

    portfolio = Portfolio(user_account_id=user_account_id, linked_account_id=linked_account.id)
    session.add(portfolio)
    session.flush()

    for order, planned_section in enumerate(plan.sections):
        section = PortfolioSection(
            portfolio_id=portfolio.id,
            section_id=planned_section.section_id,
            name=planned_section.name,
            currency=planned_section.currency,
            account_type=planned_section.account_type,
            account_sub_type=planned_section.account_sub_type,
            custom_columns=[{"key": key, "label": key, "type": "text"} for key in planned_section.detail_columns],
            display_order=order,
        )
        session.add(section)
        session.flush()

        for entry_order, holding in enumerate(planned_section.holdings):
            session.add(
                PortfolioEntry(
                    portfolio_section_id=section.id,
                    item_type=holding.item_type,
                    name=holding.name,
                    asset_class=holding.asset_class,
                    asset_type=holding.asset_type,
                    liability_type=(holding.asset_type if holding.item_type == SubAccountItemType.Liability else None),
                    currency=holding.currency,
                    units=_as_decimal(holding.units),
                    price_source=PortfolioEntryPriceSource.Manual,
                    manual_unit_price=_as_decimal(holding.unit_price),
                    manual_price_updated_at=plan.valued_at,
                    isin_code=holding.isin_code,
                    custom_values=holding.details or None,
                    display_order=entry_order,
                )
            )

    # The account now answers for itself rather than for the provider it came from.
    linked_account.provider_id = appwsrv_providers.FINBOT_PORTFOLIO_PROVIDER_ID
    linked_account.encrypted_credentials = secure.fernet_encrypt_json(
        {"portfolio_id": portfolio.id},
        environment.get_secret_key(),
    ).decode()
    linked_account.frozen = False
    try:
        session.flush()
    except IntegrityError:
        raise InvalidOperation(f"A portfolio called '{linked_account.account_name}' already exists in this account")
    return portfolio


def _find_last_successful_snapshot_entry(
    session: SessionType,
    linked_account_id: int,
) -> LinkedAccountSnapshotEntry | None:
    snapshot_entry: LinkedAccountSnapshotEntry | None = (
        session.query(LinkedAccountSnapshotEntry)
        .filter(
            LinkedAccountSnapshotEntry.linked_account_id == linked_account_id,
            LinkedAccountSnapshotEntry.success,
        )
        .order_by(LinkedAccountSnapshotEntry.snapshot_id.desc())
        .first()
    )
    return snapshot_entry


def _split_units_and_price(item_entry: Any) -> tuple[float, float]:
    """Turn a snapshot item into the portfolio's `units x unit price` representation."""
    value = item_entry.value_item_ccy
    if value is None:
        value = item_entry.value_sub_account_ccy
    value = float(value) if value is not None else 0.0
    units = float(item_entry.units) if item_entry.units is not None else None
    if units:
        return units, value / units
    return 1.0, value
