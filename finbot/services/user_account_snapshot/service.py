import json
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Generator, Optional, Protocol, cast

from sqlalchemy.orm import joinedload

from finbot import model
from finbot.apps.finbotwsrv import schema as finbotwsrv_schema
from finbot.apps.finbotwsrv.client import FinbotwsrvClient
from finbot.core import environment, fx_market
from finbot.core import schema as core_schema
from finbot.core import secure, utils
from finbot.core.db.session import Session
from finbot.core.schema import ApplicationErrorData
from finbot.core.serialization import serialize
from finbot.core.utils import unwrap_optional
from finbot.providers import schema as providers_schema
from finbot.services.user_account_snapshot import schema

FINBOT_ENV = environment.get()


@dataclass
class LinkedAccountSnapshotRequest:
    linked_account_id: int
    provider_id: str
    credentials_data: dict[Any, Any]
    line_items: list[finbotwsrv_schema.LineItem]
    user_account_currency: providers_schema.CurrencyCode


@dataclass
class LinkedAccountSnapshotResult:
    request: LinkedAccountSnapshotRequest
    snapshot_data: finbotwsrv_schema.GetFinancialDataResponse | ApplicationErrorData


@dataclass
class SnapshotErrorEntry:
    scope: str
    error: ApplicationErrorData


class SnapshotTreeVisitor(Protocol):
    def visit_linked_account(
        self,
        linked_account_snapshot: LinkedAccountSnapshotResult,
        errors: list[SnapshotErrorEntry],
    ) -> None:
        return

    def visit_sub_account(
        self,
        linked_account_snapshot: LinkedAccountSnapshotResult,
        sub_account: providers_schema.Account,
        balance: float,
    ) -> None:
        return

    def visit_sub_account_item(
        self,
        linked_account_snapshot: LinkedAccountSnapshotResult,
        sub_account: providers_schema.Account,
        item: providers_schema.Asset | providers_schema.Liability,
    ) -> None:
        return


def visit_snapshot_tree(
    raw_snapshot: list[LinkedAccountSnapshotResult], visitor: SnapshotTreeVisitor
) -> None:
    def visit_balances_first(data: finbotwsrv_schema.LineItemResults) -> int:
        if data.line_item == finbotwsrv_schema.LineItem.Balances:
            return 0
        return 1

    def iter_errors(
        snapshot: LinkedAccountSnapshotResult,
    ) -> Generator[SnapshotErrorEntry, None, None]:
        snapshot_data = snapshot.snapshot_data
        if isinstance(snapshot_data, ApplicationErrorData):
            yield SnapshotErrorEntry(scope="linked_account", error=snapshot_data)
            return
        for snapshot_data_entry in snapshot_data.financial_data:
            if isinstance(snapshot_data_entry, finbotwsrv_schema.LineItemError):
                yield SnapshotErrorEntry(
                    scope=f"linked_account.{snapshot_data_entry.line_item.name}",
                    error=snapshot_data_entry.error,
                )

    for linked_account_snapshot in raw_snapshot:
        linked_account_errors = list(iter_errors(linked_account_snapshot))
        visitor.visit_linked_account(linked_account_snapshot, linked_account_errors)
        if linked_account_errors:
            continue
        assert isinstance(
            linked_account_snapshot.snapshot_data,
            finbotwsrv_schema.GetFinancialDataResponse,
        )
        financial_data = linked_account_snapshot.snapshot_data.financial_data
        for entry in sorted(financial_data, key=visit_balances_first):
            assert isinstance(
                entry,
                (
                    finbotwsrv_schema.BalancesResults,
                    finbotwsrv_schema.AssetsResults,
                    finbotwsrv_schema.LiabilitiesResults,
                ),
            )
            for result in entry.results:
                if isinstance(result, providers_schema.BalanceEntry):
                    visitor.visit_sub_account(
                        linked_account_snapshot=linked_account_snapshot,
                        sub_account=result.account,
                        balance=result.balance,
                    )
                elif isinstance(result, providers_schema.AssetsEntry):
                    for asset in result.assets:
                        visitor.visit_sub_account_item(
                            linked_account_snapshot=linked_account_snapshot,
                            sub_account=result.account,
                            item=asset,
                        )
                elif isinstance(result, providers_schema.LiabilitiesEntry):
                    for liability in result.liabilities:
                        visitor.visit_sub_account_item(
                            linked_account_snapshot=linked_account_snapshot,
                            sub_account=result.account,
                            item=liability,
                        )


class XccyCollector(SnapshotTreeVisitor):
    def __init__(self, target_ccy: str) -> None:
        self.target_ccy = target_ccy
        self.xccys: set[fx_market.Xccy] = set()

    def visit_sub_account(
        self,
        linked_account_snapshot: LinkedAccountSnapshotResult,
        sub_account: providers_schema.Account,
        balance: float,
    ) -> None:
        if sub_account.iso_currency != self.target_ccy:
            self.xccys.add(
                fx_market.Xccy(
                    domestic=sub_account.iso_currency, foreign=self.target_ccy
                )
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


class SnapshotBuilderVisitor(SnapshotTreeVisitor):
    def __init__(
        self,
        snapshot: model.UserAccountSnapshot,
        xccy_rates_getter: CachedXccyRatesGetter,
        target_ccy: str,
    ):
        self.snapshot = snapshot
        self.xccy_rates_getter = xccy_rates_getter
        self.target_ccy = target_ccy
        self.linked_accounts: dict[
            int, model.LinkedAccountSnapshotEntry
        ] = {}  # linked_account_id -> account
        self.sub_accounts: dict[
            tuple[int, str], model.SubAccountSnapshotEntry
        ] = {}  # link_account_id, sub_account_id -> sub_account
        self.results_count = schema.SnapshotResultsCount(total=0, failures=0)

    def visit_linked_account(
        self,
        linked_account_snapshot: LinkedAccountSnapshotResult,
        errors: list[SnapshotErrorEntry],
    ) -> None:
        snapshot = self.snapshot
        linked_account_id = linked_account_snapshot.request.linked_account_id
        assert linked_account_id not in self.linked_accounts
        linked_account_entry = model.LinkedAccountSnapshotEntry(
            linked_account_id=linked_account_id
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
        linked_account_snapshot: LinkedAccountSnapshotResult,
        sub_account: providers_schema.Account,
        balance: float,
    ) -> None:
        linked_account_id = linked_account_snapshot.request.linked_account_id
        linked_account = self.linked_accounts[linked_account_id]
        assert (linked_account_id, sub_account.id) not in self.sub_accounts
        sub_account_entry = model.SubAccountSnapshotEntry(
            sub_account_id=sub_account.id,
            sub_account_ccy=sub_account.iso_currency,
            sub_account_description=sub_account.name,
            sub_account_type=sub_account.type,
        )
        linked_account.sub_accounts_entries.append(sub_account_entry)  # type: ignore
        self.sub_accounts[(linked_account_id, sub_account.id)] = sub_account_entry

    def visit_sub_account_item(
        self,
        linked_account_snapshot: LinkedAccountSnapshotResult,
        sub_account: providers_schema.Account,
        item: providers_schema.Asset | providers_schema.Liability,
    ) -> None:
        linked_account_id = linked_account_snapshot.request.linked_account_id
        sub_account_entry = self.sub_accounts[(linked_account_id, sub_account.id)]
        asset_class: providers_schema.AssetClass | None = getattr(
            item, "asset_class", None
        )
        asset_type: providers_schema.AssetType | None = getattr(
            item, "asset_type", None
        )
        new_item = model.SubAccountItemSnapshotEntry(  # type: ignore
            item_type=self._get_item_type(item),
            name=item.name,
            item_subtype=item.type,
            asset_class=asset_class.value if asset_class else None,
            asset_type=asset_type.value if asset_type else None,
            units=getattr(item, "units", None),
            value_sub_account_ccy=item.value,
            value_snapshot_ccy=item.value
            * self.xccy_rates_getter(
                fx_market.Xccy(
                    domestic=sub_account.iso_currency, foreign=self.target_ccy
                )
            ),
            provider_specific_data=item.provider_specific,
        )
        sub_account_entry.items_entries.append(new_item)  # type: ignore

    @staticmethod
    def _get_item_type(item: providers_schema.ItemType) -> model.SubAccountItemType:
        if isinstance(item, providers_schema.Asset):
            return model.SubAccountItemType.Asset
        if isinstance(item, providers_schema.Liability):
            return model.SubAccountItemType.Liability
        raise ValueError(f"unsupported item type: {type(item).__name__}")


def dispatch_snapshot_entry(
    snap_request: LinkedAccountSnapshotRequest,
) -> LinkedAccountSnapshotResult:
    try:
        logging.info(
            f"starting snapshot for linked_account_id={snap_request.linked_account_id}'"
            f" provider_id={snap_request.provider_id}"
        )

        finbot_client = FinbotwsrvClient.create()
        account_snapshot = finbot_client.get_financial_data(
            provider_id=snap_request.provider_id,
            credentials_data=snap_request.credentials_data,
            line_items=snap_request.line_items,
            user_account_currency=snap_request.user_account_currency,
        )

        logging.info(
            f"snapshot complete for for linked_account_id={snap_request.linked_account_id}'"
            f" provider_id={snap_request.provider_id}"
        )

        return LinkedAccountSnapshotResult(snap_request, account_snapshot)
    except Exception as e:
        logging.warning(
            f"fatal error while taking snapshot for linked_account_id={snap_request.linked_account_id}"
            f" provider_id={snap_request.provider_id}"
            f" error: {e}"
            f" trace:\n{traceback.format_exc()}"
        )
        return LinkedAccountSnapshotResult(
            snap_request, ApplicationErrorData.from_exception(e)
        )


def get_credentials_data(
    linked_account: model.LinkedAccount,
) -> core_schema.CredentialsPayloadType:
    assert linked_account.encrypted_credentials is not None
    return cast(
        core_schema.CredentialsPayloadType,
        json.loads(
            secure.fernet_decrypt(
                linked_account.encrypted_credentials.encode(),
                FINBOT_ENV.secret_key.encode(),
            ).decode()
        ),
    )


def take_raw_snapshot(
    user_account: model.UserAccount,
    linked_account_ids: Optional[list[int]],
) -> list[LinkedAccountSnapshotResult]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        logging.info("initializing accounts snapshot requests")
        requests = [
            LinkedAccountSnapshotRequest(
                linked_account_id=linked_account.id,
                provider_id=linked_account.provider_id,
                credentials_data=get_credentials_data(linked_account),
                line_items=[
                    finbotwsrv_schema.LineItem.Balances,
                    finbotwsrv_schema.LineItem.Assets,
                    finbotwsrv_schema.LineItem.Liabilities,
                ],
                user_account_currency=providers_schema.CurrencyCode(
                    user_account.settings.valuation_ccy
                ),
            )
            for linked_account in user_account.linked_accounts
            if not linked_account.deleted
            and not linked_account.frozen
            and (not linked_account_ids or linked_account.id in linked_account_ids)
        ]

        logging.info(f"starting snapshot with {len(requests)} request(s)")
        snapshot_entries = executor.map(dispatch_snapshot_entry, requests)
        logging.info("complete snapshot taken")
        return list(snapshot_entries)


def validate_fx_rates(rates: dict[fx_market.Xccy, Optional[float]]) -> None:
    missing_rates = [str(pair) for (pair, rate) in rates.items() if rate is None]
    if missing_rates:
        raise RuntimeError(
            f"rate is missing for the following FX pair(s): {', '.join(missing_rates)}"
        )


def take_snapshot_impl(
    user_account_id: int, linked_account_ids: Optional[list[int]], db_session: Session
) -> schema.SnapshotSummary:
    logging.info(
        f"fetching user information for"
        f" user_account_id={user_account_id}"
        f" linked_account_ids={linked_account_ids}"
    )

    user_account = (
        db_session.query(model.UserAccount)  # type: ignore
        .options(joinedload(model.UserAccount.linked_accounts))
        .options(joinedload(model.UserAccount.settings))
        .filter_by(id=user_account_id)
        .first()
    )

    logging.info(
        f"starting snapshot for user account "
        f"linked to {len(user_account.linked_accounts)} external accounts"
    )

    requested_ccy = user_account.settings.valuation_ccy
    logging.info(f"requested valuation currency is {requested_ccy}")

    with db_session.persist(model.UserAccountSnapshot()) as new_snapshot:
        new_snapshot.status = model.SnapshotStatus.Processing
        new_snapshot.requested_ccy = requested_ccy
        new_snapshot.user_account_id = user_account_id
        new_snapshot.start_time = utils.now_utc()

    raw_snapshot = take_raw_snapshot(
        user_account=user_account, linked_account_ids=linked_account_ids
    )
    xccy_collector = XccyCollector(requested_ccy)
    visit_snapshot_tree(raw_snapshot, xccy_collector)
    xccy_rates = fx_market.get_rates(xccy_collector.xccys)

    logging.debug("adding cross currency rates to snapshot")

    with db_session.persist(new_snapshot):
        new_snapshot.xccy_rates_entries.extend(
            [
                model.XccyRateSnapshotEntry(
                    xccy_pair=str(xccy), rate=Decimal(unwrap_optional(rate))
                )
                for xccy, rate in xccy_rates.items()
            ]
        )

    logging.debug("building final snapshot")

    snapshot_builder = SnapshotBuilderVisitor(
        new_snapshot, CachedXccyRatesGetter(xccy_rates), new_snapshot.requested_ccy
    )

    with db_session.persist(new_snapshot):
        visit_snapshot_tree(raw_snapshot, snapshot_builder)
        new_snapshot.status = model.SnapshotStatus.Success
        new_snapshot.end_time = utils.now_utc()

    return schema.SnapshotSummary(
        identifier=new_snapshot.id,
        start_time=new_snapshot.start_time,
        end_time=new_snapshot.end_time,
        results_count=snapshot_builder.results_count,
    )


class UserAccountSnapshotService(object):
    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def take_snapshot(
        self, user_account_id: int, linked_account_ids: list[int] | None = None
    ) -> schema.TakeSnapshotResponse:
        return schema.TakeSnapshotResponse(
            snapshot=take_snapshot_impl(
                user_account_id=user_account_id,
                linked_account_ids=linked_account_ids,
                db_session=self._db_session,
            )
        )
