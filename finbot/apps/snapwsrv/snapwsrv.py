from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional
from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload
from copy import deepcopy
from finbot.clients.finbot import FinbotClient, LineItem
from finbot.providers.plaid_us import pack_credentials as pack_plaid_credentials
from finbot.core import secure, utils, dbutils, fx_market, tracer
from finbot.core.utils import configure_logging
from finbot.apps.support import request_handler, make_error
from finbot.model import (
    UserAccount,
    UserAccountSnapshot,
    SnapshotStatus,
    LinkedAccount,
    LinkedAccountSnapshotEntry,
    SubAccountSnapshotEntry,
    SubAccountItemSnapshotEntry,
    SubAccountItemType,
    XccyRateSnapshotEntry
)
import logging.config
import logging
import os
import json
import stackprinter


def load_secret(path):
    with open(path) as secret_file:
        return secret_file.read()


configure_logging()
secret = load_secret(os.environ["FINBOT_SECRET_PATH"])
db_engine = create_engine(os.environ['FINBOT_DB_URL'])
db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))
tracer.configure(
    identity="snapwsrv",
    persistence_layer=tracer.DBPersistenceLayer(db_session)
)

app = Flask(__name__)


@app.teardown_appcontext
def cleanup_context(*args, **kwargs):
    db_session.remove()


class SnapshotTreeVisitor(object):
    def visit_account(self, account, errors):
        pass

    def visit_sub_account(self, account, sub_account, balance):
        pass

    def visit_item(self, account, sub_account, item_type, item):
        pass


@dataclass(frozen=True, eq=True)
class Xccy(object):
    domestic: str
    foreign: str

    def __str__(self):
        return f"{self.domestic}{self.foreign}"

    def serialize(self):
        return {
            "domestic": self.domestic,
            "foreign": self.foreign
        }


def visit_snapshot_tree(raw_snapshot, visitor):
    def balance_has_priority(data):
        if data["line_item"] == "balances":
            return 0
        return 1

    def iter_errors(account_data):
        if "error" in account_data:
            yield {
                "scope": "linked_account",
                "error": account_data["error"]
            }
            return
        for data_entry in account_data["financial_data"]:
            if "error" in data_entry:
                yield {
                    "scope": f"linked_account.{data_entry['line_item']}",
                    "error": data_entry["error"]
                }

    for account in raw_snapshot:
        real_account = {"id": account["account_id"], "provider": account["provider"]}
        account_errors = list(iter_errors(account["data"]))
        visitor.visit_account(real_account, account_errors)
        if account_errors:
            continue
        for entry in sorted(account["data"]["financial_data"], key=balance_has_priority):
            line_item = entry["line_item"]
            for result in entry["results"]:
                sub_account = deepcopy(result["account"])
                if line_item == "balances":
                    visitor.visit_sub_account(
                        real_account,
                        sub_account,
                        result["balance"])
                elif line_item == "assets":
                    for asset in result["assets"]:
                        visitor.visit_item(
                            real_account,
                            sub_account,
                            SubAccountItemType.Asset,
                            deepcopy(asset))
                elif line_item == "liabilities":
                    for liability in result["liabilities"]:
                        visitor.visit_item(
                            real_account,
                            sub_account,
                            SubAccountItemType.Liability,
                            deepcopy(liability))


class XccyCollector(SnapshotTreeVisitor):
    def __init__(self, target_ccy):
        self.target_ccy = target_ccy
        self.xccys = set()

    def visit_sub_account(self, account, sub_account, balance):
        if sub_account["iso_currency"] != self.target_ccy:
            self.xccys.add(Xccy(sub_account["iso_currency"], self.target_ccy))


class CachedXccyRatesGetter(object):
    def __init__(self, xccy_rates):
        self.xccy_rates = xccy_rates

    def __call__(self, xccy: Xccy):
        if xccy.foreign == xccy.domestic:
            return 1.0
        return self.xccy_rates[xccy]


class SnapshotResultsCount(object):
    def __init__(self, total=0, failures=0):
        self.total = total
        self.failures = failures

    @property
    def success(self):
        return self.total - self.failures


class SnapshotBuilderVisitor(SnapshotTreeVisitor):
    def __init__(self,
                 snapshot: UserAccountSnapshot,
                 xccy_rates_getter,
                 target_ccy):
        self.snapshot = snapshot
        self.xccy_rates_getter = xccy_rates_getter
        self.target_ccy = target_ccy
        self.linked_accounts = {}  # linked_account_id -> account
        self.sub_accounts = {}  # link_account_id, sub_account_id -> sub_account
        self.results_count = SnapshotResultsCount()

    def visit_account(self, account, errors):
        snapshot = self.snapshot
        account_id = account["id"]
        assert account_id not in self.linked_accounts
        linked_account_entry = LinkedAccountSnapshotEntry(
            linked_account_id=account_id)
        linked_account_entry.success = not bool(errors)
        self.results_count.total += 1
        if errors:
            self.results_count.failures += 1
            linked_account_entry.failure_details = errors
        snapshot.linked_accounts_entries.append(linked_account_entry)
        self.linked_accounts[account_id] = linked_account_entry

    def visit_sub_account(self, account, sub_account, balance):
        account_id = account["id"]
        linked_account = self.linked_accounts[account_id]
        sub_account_id = sub_account["id"]
        assert sub_account_id not in self.sub_accounts
        sub_account_entry = SubAccountSnapshotEntry(
            sub_account_id=sub_account_id,
            sub_account_ccy=sub_account["iso_currency"],
            sub_account_description=sub_account["name"],
            sub_account_type=sub_account["type"])
        linked_account.sub_accounts_entries.append(sub_account_entry)
        self.sub_accounts[(account_id, sub_account_id)] = sub_account_entry

    def visit_item(self, account, sub_account, item_type, item):
        linked_account_id = account["id"]
        sub_account_id = sub_account["id"]
        sub_account_entry = self.sub_accounts[(linked_account_id, sub_account_id)]
        item_value = item["value"]
        new_item = SubAccountItemSnapshotEntry(
            item_type=item_type,
            name=item["name"],
            item_subtype=item["type"],
            units=item.get("units"),
            value_sub_account_ccy=item_value,
            value_snapshot_ccy=item_value * self.xccy_rates_getter(
                Xccy(sub_account["iso_currency"], self.target_ccy)))
        sub_account_entry.items_entries.append(new_item)


class AccountSnapshotRequest(object):
    def __init__(self, account_id, provider_id, credentials_data, line_items, tracer_context=None):
        self.account_id = account_id
        self.provider_id = provider_id
        self.credentials_data = credentials_data
        self.line_items = line_items
        self.tracer_context = tracer_context


def dispatch_snapshot_entry(request: AccountSnapshotRequest):
    try:
        logging.info(f"starting snapshot for account_id={request.account_id}'"
                     f" provider_id={request.provider_id}")

        finbot_client = FinbotClient(os.environ["FINBOT_FINBOTWSRV_ENDPOINT"])
        account_snapshot = finbot_client.get_financial_data(
            provider=request.provider_id,
            credentials_data=request.credentials_data,
            line_items=request.line_items,
            tracer_context=request.tracer_context)

        logging.info(f"snapshot complete for for account_id={request.account_id}'"
                     f" provider_id={request.provider_id}")

        return request, account_snapshot
    except Exception as e:
        trace = stackprinter.format()
        logging.warning(f"fatal error while taking snapshot for account_id={request.account_id}"
                        f" provider_id={request.provider_id}"
                        f" error: {e}"
                        f" trace:\n{trace}")
        return request, make_error(
            user_message="error while taking account snapshot",
            debug_message=str(e),
            trace=trace)


def get_credentials_data(linked_account: LinkedAccount, user_account: UserAccount):
    credentials = json.loads(secure.fernet_decrypt(
        linked_account.encrypted_credentials.encode(),
        secret).decode())
    if linked_account.provider_id == "plaid_us":
        logging.info(credentials)
        return pack_plaid_credentials(credentials, user_account.plaid_settings)
    return credentials


def take_raw_snapshot(user_account, linked_accounts: Optional[List[int]]):
    with ThreadPoolExecutor(max_workers=4) as executor:
        logging.info("initializing accounts snapshot requests")
        requests = [
            AccountSnapshotRequest(
                account_id=linked_account.id,
                provider_id=linked_account.provider_id,
                credentials_data=get_credentials_data(linked_account, user_account),
                line_items=[
                    LineItem.Balances,
                    LineItem.Assets,
                    LineItem.Liabilities
                ],
                tracer_context=tracer.propagate()
            )
            for linked_account in user_account.linked_accounts
            if not linked_account.deleted
            and (not linked_accounts or linked_account.id in linked_accounts)
        ]

        logging.info(f"starting snapshot with {len(requests)} request(s)")
        snapshot_entries = executor.map(dispatch_snapshot_entry, requests)
        logging.info("complete snapshot taken")

        return [
            {
                "provider": request.provider_id,
                "account_id": request.account_id,
                "data": account_snapshot
            }
            for request, account_snapshot in snapshot_entries
        ]


def take_snapshot_impl(user_account_id: int, linked_accounts: Optional[List[int]]):
    logging.info(f"fetching user information for user account id {user_account_id}")

    user_account = (db_session.query(UserAccount)
                              .options(joinedload(UserAccount.linked_accounts))
                              .options(joinedload(UserAccount.settings))
                              .options(joinedload(UserAccount.plaid_settings))
                              .filter_by(id=user_account_id)
                              .first())

    logging.info(f"starting snapshot for user account "
                 f"linked to {len(user_account.linked_accounts)} external accounts")

    requested_ccy = user_account.settings.valuation_ccy
    logging.info(f"requested valuation currency is {requested_ccy}")

    with db_session.persist(UserAccountSnapshot()) as new_snapshot:
        new_snapshot.status = SnapshotStatus.Processing
        new_snapshot.requested_ccy = requested_ccy
        new_snapshot.user_account_id = user_account_id
        new_snapshot.start_time = utils.now_utc()

    logging.info(f"blank snapshot {new_snapshot.id} created")

    with tracer.sub_step("raw snapshot") as step:
        raw_snapshot = take_raw_snapshot(
            user_account=user_account,
            linked_accounts=linked_accounts)
        logging.info(utils.pretty_dump(raw_snapshot))
        step.set_output(raw_snapshot)

    with tracer.sub_step("fetch currency pairs"):
        xccy_collector = XccyCollector(requested_ccy)
        visit_snapshot_tree(raw_snapshot, xccy_collector)
        xccy_rates = {
            xccy: fx_market.get_xccy_rate(xccy.domestic, xccy.foreign)
            for xccy in xccy_collector.xccys
        }

    logging.info(f"adding cross currency rates to snapshot")

    with db_session.persist(new_snapshot):
        new_snapshot.xccy_rates_entries.extend([
            XccyRateSnapshotEntry(xccy_pair=str(xccy), rate=rate)
            for xccy, rate in xccy_rates.items()
        ])

    logging.info("building final snapshot")

    snapshot_builder = SnapshotBuilderVisitor(
        new_snapshot,
        CachedXccyRatesGetter(xccy_rates),
        new_snapshot.requested_ccy)

    with db_session.persist(new_snapshot):
        visit_snapshot_tree(raw_snapshot, snapshot_builder)
        new_snapshot.status = SnapshotStatus.Success
        new_snapshot.end_time = utils.now_utc()

    return jsonify({
        "snapshot": {
            "identifier": new_snapshot.id,
            "start_time": new_snapshot.start_time.isoformat(),
            "end_time": new_snapshot.end_time.isoformat(),
            "results_count": {
                "total": snapshot_builder.results_count.total,
                "success": snapshot_builder.results_count.success,
                "failures": snapshot_builder.results_count.failures
            }
        }
    })


@app.route("/healthy", methods=["GET"])
@request_handler()
def healthy():
    return jsonify({
        "healthy": True
    })


@app.route("/snapshot/<user_account_id>/take", methods=["POST"])
@request_handler(schema={
    "type": "object",
    "additionalProperties": True,
    "required": [],
    "properties": {
        "linked_accounts": {
            "type": ["array", "null"],
            "items": {
                "type": "number"
            }
        }
    }
})
def take_snapshot(user_account_id):
    data = request.json
    return take_snapshot_impl(
        user_account_id=user_account_id,
        linked_accounts=data.get("linked_accounts"))
