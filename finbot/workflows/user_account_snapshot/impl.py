import logging
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Generator, Optional, Protocol, TypedDict, cast

from sqlalchemy.orm import joinedload

from finbot import model
from finbot.core import fx_market, utils
from finbot.core import schema as core_schema
from finbot.core.schema import ApplicationErrorData
from finbot.core.serialization import serialize
from finbot.core.utils import some
from finbot.model import PersistScope, SessionType
from finbot.providers import schema as providers_schema
from finbot.workflows.fetch_financial_data import schema as finbotwsrv_schema
from finbot.workflows.user_account_snapshot import schema

logger = logging.getLogger(__name__)


@dataclass
class SnapshotErrorEntry:
    scope: str
    error: ApplicationErrorData


class SnapshotTreeVisitor(Protocol):
    def visit_linked_account(
        self,
        linked_account_id: int,
        errors: list[SnapshotErrorEntry],
    ) -> None:
        return

    def visit_sub_account(
        self,
        linked_account_id: int,
        sub_account: providers_schema.Account,
    ) -> None:
        return

    def visit_sub_account_item(
        self,
        linked_account_id: int,
        sub_account: providers_schema.Account,
        item: providers_schema.Asset | providers_schema.Liability,
    ) -> None:
        return


class LinkedAccountSnapshotWrapper:
    def __init__(
        self,
        snapshot: schema.LinkedAccountSnapshotResponse,
    ) -> None:
        self.snapshot = snapshot
        self.snapshot_data = snapshot.snapshot_data
        self.linked_account_id = snapshot.request.linked_account_id

    def iter_errors(
        self,
    ) -> Generator[SnapshotErrorEntry, None, None]:
        if isinstance(self.snapshot_data, ApplicationErrorData):
            yield SnapshotErrorEntry(scope="linked_account", error=self.snapshot_data)
            return
        for entry in self.snapshot_data.financial_data:
            if isinstance(entry, finbotwsrv_schema.LineItemError):
                yield SnapshotErrorEntry(
                    scope=f"linked_account.{entry.line_item.name}",
                    error=entry.error,
                )

    def iter_sub_accounts(
        self,
    ) -> Generator[providers_schema.Account, None, None]:
        if isinstance(self.snapshot_data, ApplicationErrorData):
            return
        for snapshot_entry in self.snapshot_data.financial_data:
            if isinstance(snapshot_entry, finbotwsrv_schema.AccountsResults):
                yield from iter(snapshot_entry.results)

    def iter_sub_accounts_items_entries(
        self,
    ) -> Generator[providers_schema.AssetsEntry | providers_schema.LiabilitiesEntry, None, None]:
        if isinstance(self.snapshot_data, ApplicationErrorData):
            return
        for snapshot_entry in self.snapshot_data.financial_data:
            if isinstance(snapshot_entry, (finbotwsrv_schema.AssetsResults, finbotwsrv_schema.LiabilitiesResults)):
                for result_entry in snapshot_entry.results:
                    yield result_entry


def visit_snapshot_tree(
    raw_snapshot: list[schema.LinkedAccountSnapshotResponse],
    visitor: SnapshotTreeVisitor,
) -> None:
    for linked_account_snapshot in raw_snapshot:
        snapshot_wrapper = LinkedAccountSnapshotWrapper(linked_account_snapshot)
        linked_account_errors = list(snapshot_wrapper.iter_errors())
        visitor.visit_linked_account(linked_account_id=snapshot_wrapper.linked_account_id, errors=linked_account_errors)
        if linked_account_errors:
            continue
        mapped_sub_accounts: dict[str, providers_schema.Account] = {}
        for sub_account in snapshot_wrapper.iter_sub_accounts():
            mapped_sub_accounts[sub_account.id] = sub_account
            visitor.visit_sub_account(
                linked_account_id=snapshot_wrapper.linked_account_id,
                sub_account=sub_account,
            )
        for entries in snapshot_wrapper.iter_sub_accounts_items_entries():
            sub_account = mapped_sub_accounts[entries.account_id]
            for item in entries.items:
                visitor.visit_sub_account_item(
                    linked_account_id=snapshot_wrapper.linked_account_id,
                    sub_account=sub_account,
                    item=item,
                )


class XccyCollector(SnapshotTreeVisitor):
    def __init__(self, target_ccy: core_schema.CurrencyCode) -> None:
        self.target_ccy = target_ccy
        self.xccys: set[fx_market.Xccy] = set()

    def visit_sub_account(
        self,
        linked_account_id: core_schema.LinkedAccountId,
        sub_account: providers_schema.Account,
    ) -> None:
        self._collect(sub_account.iso_currency, self.target_ccy)

    def visit_sub_account_item(
        self,
        linked_account_id: core_schema.LinkedAccountId,
        sub_account: providers_schema.Account,
        item: providers_schema.Asset | providers_schema.Liability,
    ) -> None:
        if item.value_in_item_ccy is not None:
            self._collect(item.currency, sub_account.iso_currency)
        else:
            self._collect(sub_account.iso_currency, item.currency)

    def _collect(self, domestic: core_schema.CurrencyCode, foreign: core_schema.CurrencyCode) -> None:
        if domestic != foreign:
            self.xccys.add(
                fx_market.Xccy(
                    domestic=domestic,
                    foreign=foreign,
                ),
            )


class CachedXccyRatesGetter(object):
    def __init__(self, xccy_rates: dict[fx_market.Xccy, float | None]) -> None:
        self.xccy_rates: dict[fx_market.Xccy, float] = {
            xccy: rate for (xccy, rate) in xccy_rates.items() if rate is not None
        }

    def __call__(self, xccy: fx_market.Xccy) -> float:
        if xccy.foreign == xccy.domestic:
            return 1.0
        return self.xccy_rates[xccy]


class ItemValuationFields(TypedDict):
    value_item_ccy: float | None
    value_sub_account_ccy: float
    value_snapshot_ccy: float


class SnapshotBuilderVisitor(SnapshotTreeVisitor):
    def __init__(
        self,
        snapshot: model.UserAccountSnapshot,
        xccy_rates_getter: CachedXccyRatesGetter,
        target_ccy: str,
        selected_sub_accounts: dict[core_schema.LinkedAccountId, list[providers_schema.SubAccountId] | None],
    ):
        self.snapshot = snapshot
        self.xccy_rates_getter = xccy_rates_getter
        self.target_ccy = target_ccy
        self.selected_sub_accounts = selected_sub_accounts
        self.seen_sub_accounts: dict[core_schema.LinkedAccountId, set[providers_schema.SubAccountId]] = defaultdict(set)
        self.linked_accounts: dict[int, model.LinkedAccountSnapshotEntry] = {}  # linked_account_id -> account
        self.sub_accounts: dict[
            tuple[core_schema.LinkedAccountId, providers_schema.SubAccountId], model.SubAccountSnapshotEntry
        ] = {}
        self.results_count = schema.SnapshotResultsCount(total=0, failures=0)

    def visit_linked_account(
        self,
        linked_account_id: core_schema.LinkedAccountId,
        errors: list[SnapshotErrorEntry],
    ) -> None:
        snapshot = self.snapshot
        assert linked_account_id not in self.linked_accounts
        linked_account_entry = model.LinkedAccountSnapshotEntry(
            linked_account_id=linked_account_id,
        )
        linked_account_entry.success = not bool(errors)
        self.results_count.total += 1
        if errors:
            self.results_count.failures += 1
            linked_account_entry.failure_details = serialize(errors)
        snapshot.linked_accounts_entries.append(linked_account_entry)
        self.linked_accounts[linked_account_id] = linked_account_entry

    def visit_sub_account(
        self,
        linked_account_id: core_schema.LinkedAccountId,
        sub_account: providers_schema.Account,
    ) -> None:
        self.seen_sub_accounts[linked_account_id].add(sub_account.id)
        if not self._include_sub_account(linked_account_id, sub_account.id):
            return
        linked_account = self.linked_accounts[linked_account_id]
        assert (linked_account_id, sub_account.id) not in self.sub_accounts
        sub_account_entry = model.SubAccountSnapshotEntry(
            sub_account_id=sub_account.id,
            sub_account_ccy=sub_account.iso_currency,
            sub_account_description=sub_account.name,
            sub_account_type=sub_account.type.value,
            sub_account_sub_type=sub_account.sub_type,
        )
        linked_account.sub_accounts_entries.append(sub_account_entry)  # type: ignore
        self.sub_accounts[(linked_account_id, sub_account.id)] = sub_account_entry

    def visit_sub_account_item(
        self,
        linked_account_id: core_schema.LinkedAccountId,
        sub_account: providers_schema.Account,
        item: providers_schema.Asset | providers_schema.Liability,
    ) -> None:
        if not self._include_sub_account(linked_account_id, sub_account.id):
            return
        sub_account_entry = self.sub_accounts[(linked_account_id, sub_account.id)]
        item_type = self._get_item_type(item)
        asset_class = item.asset_class if isinstance(item, providers_schema.Asset) else None
        asset_type = item.asset_type if isinstance(item, providers_schema.Asset) else None
        new_item = model.SubAccountItemSnapshotEntry(  # type: ignore
            item_type=item_type,
            name=item.name,
            item_subtype=item.type,
            asset_class=asset_class.value if asset_class else None,
            asset_type=asset_type.value if asset_type else None,
            units=item.units if isinstance(item, providers_schema.Asset) else None,
            currency=item.currency if isinstance(item, providers_schema.Asset) else None,
            isin_code=item.isin_code if isinstance(item, providers_schema.Asset) else None,
            provider_specific_data=item.provider_specific,
            **self._get_item_valuation(sub_account, item),
        )
        sub_account_entry.items_entries.append(new_item)  # type: ignore

    def _get_item_valuation(
        self,
        sub_account: providers_schema.Account,
        item: providers_schema.Asset | providers_schema.Liability,
    ) -> ItemValuationFields:
        value_item_ccy = item.value_in_item_ccy
        value_sub_account_ccy = item.value_in_account_ccy
        if value_sub_account_ccy is None:
            assert value_item_ccy is not None
            value_sub_account_ccy = value_item_ccy * self.xccy_rates_getter(
                fx_market.Xccy(item.currency, sub_account.iso_currency)
            )
        else:
            assert value_item_ccy is None
        if value_item_ccy is None:
            value_item_ccy = value_sub_account_ccy * self.xccy_rates_getter(
                fx_market.Xccy(sub_account.iso_currency, item.currency)
            )
        value_snapshot_ccy = value_sub_account_ccy * self.xccy_rates_getter(
            fx_market.Xccy(sub_account.iso_currency, self.target_ccy)
        )
        return ItemValuationFields(
            value_sub_account_ccy=value_sub_account_ccy,
            value_snapshot_ccy=value_snapshot_ccy,
            value_item_ccy=value_item_ccy,
        )

    def _include_sub_account(
        self,
        linked_account_id: core_schema.LinkedAccountId,
        sub_account_id: providers_schema.SubAccountId,
    ) -> bool:
        sub_account_ids = self.selected_sub_accounts.get(linked_account_id)
        return not sub_account_ids or sub_account_id in sub_account_ids

    @staticmethod
    def _get_item_type(item: providers_schema.ItemType) -> model.SubAccountItemType:
        if isinstance(item, providers_schema.Asset):
            return model.SubAccountItemType.Asset
        if isinstance(item, providers_schema.Liability):
            return model.SubAccountItemType.Liability
        raise ValueError(f"unsupported item type: {type(item).__name__}")


def is_linked_account_included_in_snapshot(
    linked_account: model.LinkedAccount,
    linked_account_ids: list[core_schema.LinkedAccountId] | None,
) -> bool:
    if linked_account.deleted or linked_account.frozen:
        return False
    if linked_account_ids and linked_account.id not in linked_account_ids:
        return False
    return True


def prepare_raw_snapshot_requests(
    user_account: model.UserAccount,
    linked_account_ids: list[core_schema.LinkedAccountId] | None,
) -> list[schema.LinkedAccountSnapshotRequest]:
    return [
        schema.LinkedAccountSnapshotRequest(
            linked_account_id=linked_account.id,
            provider_id=linked_account.provider_id,
            encrypted_credentials=some(linked_account.encrypted_credentials),
            line_items=[
                finbotwsrv_schema.LineItem.Accounts,
                finbotwsrv_schema.LineItem.Assets,
                finbotwsrv_schema.LineItem.Liabilities,
            ],
            user_account_currency=core_schema.CurrencyCode(user_account.settings.valuation_ccy),
        )
        for linked_account in user_account.linked_accounts
        if is_linked_account_included_in_snapshot(linked_account, linked_account_ids)
    ]


def validate_fx_rates(rates: dict[fx_market.Xccy, Optional[float]]) -> None:
    missing_rates = [str(pair) for (pair, rate) in rates.items() if rate is None]
    if missing_rates:
        raise RuntimeError(f"rate is missing for the following FX pair(s): {', '.join(missing_rates)}")


def load_user_account(user_account_id: int, db_session: SessionType) -> model.UserAccount:
    return cast(
        model.UserAccount,
        db_session.query(model.UserAccount)  # type: ignore
        .options(joinedload(model.UserAccount.linked_accounts))
        .options(joinedload(model.UserAccount.settings))
        .filter_by(id=user_account_id)
        .one(),
    )


def create_empty_snapshot(
    user_account_id: int,
    db_session: SessionType,
) -> model.UserAccountSnapshot:
    persist_scope = PersistScope(db_session)
    user_account = load_user_account(user_account_id, db_session)
    requested_ccy = core_schema.CurrencyCode(user_account.settings.valuation_ccy)
    with persist_scope(model.UserAccountSnapshot()) as new_snapshot:
        new_snapshot.status = model.SnapshotStatus.Processing
        new_snapshot.requested_ccy = requested_ccy
        new_snapshot.user_account_id = user_account_id
        new_snapshot.start_time = utils.now_utc()
    return new_snapshot


def build_and_persist_final_snapshot(
    user_account: model.UserAccount,
    new_snapshot: model.UserAccountSnapshot,
    raw_snapshot: list[schema.LinkedAccountSnapshotResponse],
    db_session: SessionType,
) -> schema.SnapshotSummary:
    persist_scope = PersistScope(db_session)
    xccy_collector = XccyCollector(core_schema.CurrencyCode(new_snapshot.requested_ccy))
    visit_snapshot_tree(raw_snapshot, xccy_collector)
    xccy_rates = fx_market.get_rates(xccy_collector.xccys)

    logger.debug("adding cross currency rates to snapshot")

    with persist_scope(new_snapshot):
        new_snapshot.xccy_rates_entries.extend(
            [
                model.XccyRateSnapshotEntry(
                    xccy_pair=str(xccy),
                    rate=Decimal(some(rate)),
                )
                for xccy, rate in xccy_rates.items()
            ]
        )

    logger.debug("building final snapshot")

    snapshot_builder = SnapshotBuilderVisitor(
        snapshot=new_snapshot,
        xccy_rates_getter=CachedXccyRatesGetter(xccy_rates),
        target_ccy=new_snapshot.requested_ccy,
        selected_sub_accounts={
            linked_account.id: linked_account.selected_sub_accounts for linked_account in user_account.linked_accounts
        },
    )

    with persist_scope(new_snapshot):
        visit_snapshot_tree(raw_snapshot, snapshot_builder)
        new_snapshot.status = model.SnapshotStatus.Success
        new_snapshot.end_time = utils.now_utc()

    return schema.SnapshotSummary(
        identifier=new_snapshot.id,
        start_time=some(new_snapshot.start_time),
        end_time=new_snapshot.end_time,
        results_count=snapshot_builder.results_count,
    )
