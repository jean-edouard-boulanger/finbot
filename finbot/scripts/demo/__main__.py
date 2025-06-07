import decimal
import logging
import random
from argparse import ArgumentParser
from datetime import date, datetime, timedelta

import bcrypt

from finbot import model
from finbot.apps.appwsrv.core.formatting_rules import ACCOUNTS_PALETTE
from finbot.core.logging import configure_logging
from finbot.core.schema import CurrencyCode
from finbot.model import ScopedSession, db
from finbot.providers.schema import Asset
from finbot.scripts.demo import scenarios, sim
from finbot.scripts.demo.market import Market
from finbot.services.valuation_history_writer import ValuationHistoryWriterService

configure_logging()
logger = logging.getLogger("demo")


DEFAULT_DEMO_ACCOUNT_PASSWORD = "demo"
DEFAULT_DEMO_ACCOUNT_EMAIL = "demo@finbot.com"
TMP_EMAIL_MARKER = "+tmp"


def create_parser() -> ArgumentParser:
    parser = ArgumentParser("Finbot demo account setup")
    parser.add_argument("--email", type=str, default=DEFAULT_DEMO_ACCOUNT_EMAIL)
    parser.add_argument("--password", type=str, default=DEFAULT_DEMO_ACCOUNT_PASSWORD)
    parser.add_argument("--full-name", type=str, default="Demo")
    parser.add_argument("--valuation-ccy", type=str, default="EUR")
    parser.add_argument("--simulate-days", type=int, default=365)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def drop_demo_account(account_email: str) -> None:
    db.session.query(model.UserAccount).filter_by(email=account_email).delete()
    db.session.commit()


def tmp_email(email: str) -> str:
    prefix, suffix = email.split("@")
    return f"{prefix}{TMP_EMAIL_MARKER}@{suffix}"


def create_demo_account(
    email: str,
    password: str,
    full_name: str,
    valuation_ccy: str,
) -> model.UserAccount:
    user_account = model.UserAccount(
        email=tmp_email(email),
        password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
        full_name=full_name,
        is_demo=True,
        settings=model.UserAccountSettings(
            valuation_ccy=valuation_ccy,
        ),
    )
    db.session.add(user_account)
    db.session.commit()
    return user_account


def activate_new_demo_accounts(
    old_demo_account: model.UserAccount | None,
    new_demo_account: model.UserAccount,
) -> None:
    if old_demo_account:
        db.session.delete(old_demo_account)  # type: ignore
        db.session.flush()
    new_demo_account.email = new_demo_account.email.replace(f"{TMP_EMAIL_MARKER}@", "@")
    db.session.commit()


def create_linked_accounts_if_needed(
    sim_result: sim.SimResult,
    existing_linked_accounts: dict[str, model.LinkedAccount],
    user_account: model.UserAccount,
) -> dict[str, model.LinkedAccount]:
    for linked_account in sim_result.linked_accounts:
        if linked_account.linked_account.identifier not in existing_linked_accounts:
            new_linked_account = model.LinkedAccount(
                user_account_id=user_account.id,
                provider_id="dummy_uk",
                account_name=linked_account.linked_account.description,
                account_colour=random.choice(ACCOUNTS_PALETTE),
            )
            db.session.add(new_linked_account)
            db.session.commit()
            existing_linked_accounts[linked_account.linked_account.identifier] = new_linked_account
            logger.info(
                f"created new linked account model {new_linked_account.id}"
                f" for simulated linked account {linked_account.linked_account}"
            )
    return existing_linked_accounts


def build_sub_account_item_snapshot_entry_from_sim_result(
    current_date: date,
    valuation_ccy: CurrencyCode,
    sub_account_result: sim.SubAccountSimResult,
    item: sim.ItemType,
    market: Market,
) -> model.SubAccountItemSnapshotEntry:
    assert isinstance(item, Asset)
    if item.value_in_account_ccy is None:
        assert isinstance(item.value_in_item_ccy, float)
        rate = market.get_fx_rate(item.currency, sub_account_result.sub_account.currency, current_date)
        value_in_account_ccy = decimal.Decimal(item.value_in_item_ccy * rate)
        value_in_item_ccy = decimal.Decimal(item.value_in_item_ccy)
    else:
        assert isinstance(item.value_in_account_ccy, float)
        rate = market.get_fx_rate(sub_account_result.sub_account.currency, item.currency, current_date)
        value_in_account_ccy = decimal.Decimal(item.value_in_account_ccy)
        value_in_item_ccy = decimal.Decimal(rate * item.value_in_account_ccy)
    rate = market.get_fx_rate(sub_account_result.sub_account.currency, valuation_ccy, current_date)
    return model.SubAccountItemSnapshotEntry(
        item_type=model.SubAccountItemType.Asset,
        name=item.name,
        item_subtype=item.asset_type.value,
        asset_class=item.asset_class.value,
        asset_type=item.asset_type.value,
        units=decimal.Decimal(item.units) if item.units else None,
        value_sub_account_ccy=value_in_account_ccy,
        value_item_ccy=value_in_item_ccy,
        value_snapshot_ccy=decimal.Decimal(rate) * value_in_account_ccy,
        currency=item.currency,
    )


def build_sub_account_snapshot_entry_from_sim_result(
    current_date: date,
    valuation_ccy: CurrencyCode,
    sub_account_result: sim.SubAccountSimResult,
    market: Market,
) -> model.SubAccountSnapshotEntry:
    return model.SubAccountSnapshotEntry(  # type: ignore
        sub_account_id=sub_account_result.sub_account.identifier,
        sub_account_ccy=sub_account_result.sub_account.currency,
        sub_account_description=sub_account_result.sub_account.description,
        sub_account_type=sub_account_result.sub_account.get_type().value,
        sub_account_sub_type=sub_account_result.sub_account.get_subtype(),
        items_entries=[
            build_sub_account_item_snapshot_entry_from_sim_result(
                current_date=current_date,
                valuation_ccy=valuation_ccy,
                sub_account_result=sub_account_result,
                item=item,
                market=market,
            )
            for item in sub_account_result.items
        ],
    )


def build_linked_account_snapshot_entry_from_sim_result(
    current_date: date,
    valuation_ccy: CurrencyCode,
    linked_account_result: sim.LinkedAccountSimResult,
    mapped_linked_accounts: dict[str, model.LinkedAccount],
    market: Market,
) -> model.LinkedAccountSnapshotEntry:
    return model.LinkedAccountSnapshotEntry(  # type: ignore
        linked_account_id=mapped_linked_accounts[linked_account_result.linked_account.identifier].id,
        success=True,
        sub_accounts_entries=[
            build_sub_account_snapshot_entry_from_sim_result(
                current_date=current_date,
                valuation_ccy=valuation_ccy,
                sub_account_result=sub_account_result,
                market=market,
            )
            for sub_account_result in linked_account_result.sub_accounts
        ],
    )


def build_snapshot_from_sim_result(
    sim_result: sim.SimResult,
    user_account: model.UserAccount,
    mapped_linked_accounts: dict[str, model.LinkedAccount],
    market: Market,
) -> model.UserAccountSnapshot:
    snapshot = model.UserAccountSnapshot(
        user_account_id=user_account.id,
        status=model.SnapshotStatus.Success,
        requested_ccy=sim_result.scenario_config.valuation_ccy,
        start_time=sim_result.current_time,
        end_time=sim_result.current_time,
        linked_accounts_entries=[
            build_linked_account_snapshot_entry_from_sim_result(
                current_date=sim_result.current_date,
                valuation_ccy=sim_result.scenario_config.valuation_ccy,
                linked_account_result=linked_account_result,
                mapped_linked_accounts=mapped_linked_accounts,
                market=market,
            )
            for linked_account_result in sim_result.linked_accounts
        ],
    )
    db.session.add(snapshot)
    db.session.commit()
    return snapshot


def setup_demo() -> None:
    settings = create_parser().parse_args()
    random.seed(settings.seed)
    drop_demo_account(tmp_email(settings.email))
    demo_account = create_demo_account(
        email=settings.email,
        password=settings.password,
        full_name=settings.full_name,
        valuation_ccy=settings.valuation_ccy,
    )
    scenario_config = sim.ScenarioConfig(
        valuation_ccy=CurrencyCode("EUR"),
        start_date=datetime.now().date() - timedelta(days=settings.simulate_days),
        end_date=datetime.now().date(),
    )
    scenario = scenarios.MainScenario(config=scenario_config)
    mapped_linked_accounts: dict[str, model.LinkedAccount] = {}
    simulator = sim.Simulator(scenario)
    for sim_result in simulator.run_simulation():
        mapped_linked_accounts = create_linked_accounts_if_needed(
            sim_result=sim_result,
            existing_linked_accounts=mapped_linked_accounts,
            user_account=demo_account,
        )
        snapshot = build_snapshot_from_sim_result(
            sim_result=sim_result,
            user_account=demo_account,
            mapped_linked_accounts=mapped_linked_accounts,
            market=simulator.market,
        )
        history_writer = ValuationHistoryWriterService(db.session)
        history_writer.write_history(snapshot_id=snapshot.id)
    activate_new_demo_accounts(
        old_demo_account=db.session.query(model.UserAccount).filter_by(email=settings.email).first(),
        new_demo_account=demo_account,
    )


def main() -> None:
    with ScopedSession():
        setup_demo()


if __name__ == "__main__":
    main()
