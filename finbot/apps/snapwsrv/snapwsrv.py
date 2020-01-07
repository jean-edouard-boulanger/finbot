from dataclasses import dataclass
from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload
from copy import deepcopy
from finbot.clients.finbot import FinbotClient, LineItem
from finbot.core import crypto, utils, dbutils, fx
from finbot.apps.support import generic_request_handler
from finbot.model import (
    UserAccount,
    UserAccountSnapshot,
    SnapshotStatus,
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


logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


def load_secret(path):
    with open(path) as secret_file:
        return secret_file.read()


secret = load_secret(os.environ["FINBOT_SECRET_PATH"])
db_engine = create_engine(os.environ['FINBOT_DB_URL'])
db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))
finbot_client = FinbotClient(os.environ["FINBOT_FINBOTWSRV_ENDPOINT"])

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
        for entry in account_data["financial_data"]:
            if "error" in entry:
                yield {
                    "scope": f"linked_account.{entry['line_item']}",
                    "error": entry["error"]
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
                            "asset",
                            deepcopy(asset))


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
            sub_account_description=sub_account["name"])
        linked_account.sub_accounts_entries.append(sub_account_entry)
        self.sub_accounts[(account_id, sub_account_id)] = sub_account_entry

    def visit_item(self, account, sub_account, item_type, item):
        linked_account_id = account["id"]
        sub_account_id = sub_account["id"]
        sub_account_entry = self.sub_accounts[(linked_account_id, sub_account_id)]
        item_value = item["value"]
        new_item = SubAccountItemSnapshotEntry(
            item_type=SubAccountItemType.Asset,  # TODO (could eventually be liability)
            name=item["name"],
            item_subtype=item["type"],
            units=item.get("units"),
            value_sub_account_ccy=item_value,
            value_snapshot_ccy=item_value * self.xccy_rates_getter(
                Xccy(sub_account["iso_currency"], self.target_ccy)))
        sub_account_entry.items_entries.append(new_item)


def take_raw_snapshot(user_account):
    raw_snapshot = []
    for account in user_account.linked_accounts:
        logging.info(f"taking snapshot for external account id '{account.id}' ({account.provider_id})")
        snapshot_entry = finbot_client.get_financial_data(
            provider=account.provider_id,
            credentials_data=json.loads(
                crypto.fernet_decrypt(
                    account.encrypted_credentials.encode(),
                    secret).decode()),
            line_items=[
                LineItem.Balances,
                LineItem.Assets
            ]
        )
        raw_snapshot.append({
            "provider": account.provider_id,
            "account_id": account.id,
            "data": snapshot_entry
        })
    return raw_snapshot


@app.route("/snapshot/<user_account_id>/take", methods=["POST"])
@generic_request_handler
def take_snapshot(user_account_id):
    logging.info(f"fetching user information for user account id {user_account_id}")

    user_account = (db_session.query(UserAccount)
                              .options(joinedload(UserAccount.linked_accounts))
                              .options(joinedload(UserAccount.settings))
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

    raw_snapshot = take_raw_snapshot(user_account)
    logging.info(utils.pretty_dump(raw_snapshot))

    logging.info(f"collecting currency pairs from raw snapshot")

    xccy_collector = XccyCollector(requested_ccy)
    visit_snapshot_tree(raw_snapshot, xccy_collector)

    logging.info("fetching cross currency rates for: "
                 f"{', '.join(str(xccy) for xccy in xccy_collector.xccys)}")

    xccy_rates = {
        xccy: fx.get_xccy_rate(xccy.domestic, xccy.foreign)
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
