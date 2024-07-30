import abc
import dataclasses
import logging
import typing as t
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from finbot.core.schema import CurrencyCode
from finbot.providers import schema as providers_schema
from finbot.scripts.demo import utils as demo_utils
from finbot.scripts.demo.market import Market, TickerType

ItemType: t.TypeAlias = providers_schema.Liability | providers_schema.Asset
UnitsType: t.TypeAlias = float


@dataclass(frozen=True)
class UnitAmount:
    units: float


@dataclass(frozen=True)
class CashAmount:
    amount: float
    currency: CurrencyCode


@dataclass
class SubAccount(abc.ABC):
    identifier: str
    description: str
    currency: CurrencyCode

    @abc.abstractmethod
    def get_type(self) -> providers_schema.AccountType:
        pass

    @abc.abstractmethod
    def get_subtype(self) -> str | None:
        pass

    @abc.abstractmethod
    def get_items(
        self,
        as_of: date,
        market: Market,
    ) -> list[ItemType]:
        pass

    def sim(
        self,
        current_date: date,
        market: Market,
    ) -> None:
        pass


@dataclass
class ManualPortfolio(SubAccount):
    type_: providers_schema.AccountType
    subtype: str | None
    items: list[ItemType]

    def get_type(self) -> providers_schema.AccountType:
        return self.type_

    def get_subtype(self) -> str | None:
        return self.subtype

    def get_items(
        self,
        as_of: date,
        market: Market,
    ) -> list[ItemType]:
        return self.items


@dataclass
class BrokerageAccount(SubAccount):
    account_sub_type: str
    cash_balances: dict[CurrencyCode, float] = dataclasses.field(default_factory=dict)
    assets: dict[TickerType, UnitsType] = dataclasses.field(default_factory=dict)

    def get_type(self) -> providers_schema.AccountType:
        return providers_schema.AccountType.investment

    def get_subtype(self) -> str | None:
        return self.account_sub_type

    def deposit_cash(self, amount: UnitsType, currency: CurrencyCode) -> None:
        logging.info(f"{type(self).__name__}({self.identifier}) deposit_cash {amount=} {currency=}")
        self._update_cash_bal(currency, amount)

    def convert_cash(
        self,
        amount: CashAmount,
        to_currency: CurrencyCode,
        as_of: date,
        market: Market,
    ) -> None:
        logging.info(f"{type(self).__name__}({self.identifier}) convert_cash {amount=} {to_currency=} {as_of=}")
        assert amount.currency != to_currency
        assert amount.currency in self.cash_balances and self.cash_balances[amount.currency] >= amount.amount
        rate = market.get_fx_rate(amount.currency, to_currency, as_of)
        self._update_cash_bal(to_currency, amount.amount * rate)
        self._update_cash_bal(amount.currency, -amount.amount)

    def convert_cash_to_meet_expected_balance(
        self,
        expected: CashAmount,
        as_of: date,
        market: Market,
    ) -> None:
        logging.info(
            f"{type(self).__name__}({self.identifier}) buy_fx_to_meet_expected_balance" f" {expected=} {as_of=}"
        )
        if self.cash_balances.get(expected.currency, 0) >= expected.amount:
            return
        dest_ccy = expected.currency
        existing_bal = self.cash_balances.get(dest_ccy, 0.0)
        dest_remaining = expected.amount - existing_bal
        conversions: list[CashAmount] = []
        for source_ccy, balance in self.cash_balances.items():
            if source_ccy != dest_ccy:
                fx_rate = market.get_fx_rate(source_ccy, dest_ccy, as_of)
                amount_needed = dest_remaining / fx_rate
                converted_amount = min(amount_needed, balance)
                dest_remaining -= converted_amount * fx_rate
                conversions.append(CashAmount(converted_amount, source_ccy))
        assert dest_remaining == 0.0
        for conversion in conversions:
            self.convert_cash(conversion, dest_ccy, as_of, market)
        assert self.cash_balances[dest_ccy] >= expected.amount

    def _update_asset_units(self, ticker: TickerType, units_diff: float) -> None:
        if ticker not in self.assets and units_diff > 0:
            self.assets[ticker] = 0.0
        prev_units = self.assets.get(ticker, 0.0)
        new_units = prev_units + units_diff
        assert new_units >= 0.0
        self.assets[ticker] = new_units
        logging.info(
            f"{type(self).__name__}({self.identifier}) update_asset_units"
            f" {ticker=} {units_diff=} {prev_units=} {new_units=}"
        )
        if new_units == 0.0:
            del self.assets[ticker]

    def _update_cash_bal(self, ccy: CurrencyCode, amount_diff: float) -> None:
        if ccy not in self.cash_balances and amount_diff > 0:
            self.cash_balances[ccy] = 0.0
        prev_amount = self.cash_balances.get(ccy, 0.0)
        new_amount = prev_amount + amount_diff
        assert new_amount >= 0.0
        self.cash_balances[ccy] = new_amount
        logging.info(
            f"{type(self).__name__}({self.identifier}) update_cash_bal"
            f" {ccy=} {amount_diff=} {prev_amount=} {new_amount=}"
        )
        if new_amount == 0.0:
            del self.cash_balances[ccy]

    def buy_asset(
        self,
        ticker: TickerType,
        amount: UnitAmount | CashAmount,
        as_of: date,
        market: Market,
    ) -> None:
        logging.info(f"{type(self).__name__}({self.identifier}) buy_asset {ticker=} {amount=} {as_of=}")
        asset_ccy = market.get_ticker_currency(ticker)
        unit_value = market.get_asset_value(ticker, as_of)
        if isinstance(amount, UnitAmount):
            total_price_in_asset_ccy = unit_value * amount.units
            purchased_units = amount.units
        else:
            assert isinstance(amount, CashAmount)
            total_price_in_asset_ccy = market.get_fx_rate(amount.currency, asset_ccy, as_of) * amount.amount
            purchased_units = total_price_in_asset_ccy / unit_value
        assert purchased_units >= 0.0
        self.convert_cash_to_meet_expected_balance(
            expected=CashAmount(total_price_in_asset_ccy, asset_ccy),
            as_of=as_of,
            market=market,
        )
        self._update_cash_bal(asset_ccy, -total_price_in_asset_ccy)
        self._update_asset_units(ticker, purchased_units)

    def get_items(
        self,
        as_of: date,
        market: Market,
    ) -> list[ItemType]:
        items: list[ItemType] = []
        for currency, amount in self.cash_balances.items():
            items.append(
                providers_schema.Asset.cash(
                    currency=currency,
                    is_domestic=currency == market.valuation_ccy,
                    amount=amount,
                )
            )
        for asset_ticker, units in self.assets.items():
            asset_ccy = market.get_ticker_currency(asset_ticker)
            if market.get_ticker_info(asset_ticker)["quoteType"] == "CRYPTOCURRENCY":
                items.append(
                    providers_schema.Asset(
                        name=asset_ticker.split("-")[0],
                        asset_class=providers_schema.AssetClass.crypto,
                        asset_type=providers_schema.AssetType.crypto_currency,
                        value_in_item_ccy=market.get_asset_value(asset_ticker, as_of) * units,
                        units=units,
                        currency=asset_ccy,
                    )
                )
            else:
                items.append(
                    providers_schema.Asset(
                        name=asset_ticker,
                        asset_class=providers_schema.AssetClass.equities,
                        asset_type=providers_schema.AssetType.stock,
                        value_in_item_ccy=market.get_asset_value(asset_ticker, as_of) * units,
                        units=units,
                        currency=asset_ccy,
                    )
                )
        return items


@dataclass
class CashAccount(SubAccount):
    balance: float

    def deposit(self, amount: float) -> None:
        logging.info(f"{type(self).__name__}({self.identifier}) deposit {amount=} ({self.currency=})")
        assert amount >= 0
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        logging.info(f"{type(self).__name__}({self.identifier}) withdraw {amount=} ({self.currency=})")
        assert amount >= 0
        assert amount <= self.balance
        self.balance -= amount

    def transfer(self, amount: float, other: "CashAccount") -> None:
        assert other.currency == self.currency
        self.withdraw(amount)
        other.deposit(amount)

    def get_items(self, as_of: date, market: Market) -> list[ItemType]:
        return [
            providers_schema.Asset.cash(
                currency=self.currency,
                is_domestic=True,
                amount=self.balance,
            )
        ]


class CheckingAccount(CashAccount):
    def get_type(self) -> providers_schema.AccountType:
        return providers_schema.AccountType.depository

    def get_subtype(self) -> str | None:
        return "checking"


@dataclass
class SavingsAccount(CashAccount):
    yearly_rate: float
    accrued: float = 0.0
    payment_frequency: t.Literal["daily", "weekly", "monthly", "yearly"] = "yearly"

    def get_type(self) -> providers_schema.AccountType:
        return providers_schema.AccountType.depository

    def get_subtype(self) -> str | None:
        return "savings"

    def _deposit_accruals(self) -> None:
        self.balance += self.accrued
        self.accrued = 0

    def sim(self, current_date: date, market: Market) -> None:
        self.accrued += self.balance * (self.yearly_rate / 364)
        if (
            self.payment_frequency == "daily"
            or (self.payment_frequency == "weekly" and demo_utils.is_last_day_of_week(current_date))
            or (self.payment_frequency == "monthly" and demo_utils.is_last_day_of_month(current_date))
            or (self.payment_frequency == "yearly" and demo_utils.is_last_day_of_year(current_date))
        ):
            self._deposit_accruals()


@dataclass
class LinkedAccount:
    identifier: str
    description: str
    sub_accounts: list[SubAccount]

    def get_sub_account(self, identifier: str) -> SubAccount:
        for sub_account in self.sub_accounts:
            if sub_account.identifier == identifier:
                return sub_account
        raise ValueError(f"No such sub account: {identifier}")


@dataclass
class SimulationState:
    linked_accounts: list[LinkedAccount]

    def get_linked_account(self, identifier: str) -> LinkedAccount:
        for linked_account in self.linked_accounts:
            if linked_account.identifier == identifier:
                return linked_account
        raise ValueError(f"No such linked account: {identifier}")

    def get_sub_account(self, linked_account_id: str, sub_account_id: str) -> SubAccount:
        return self.get_linked_account(linked_account_id).get_sub_account(sub_account_id)

    def iter_sub_accounts(self) -> t.Generator[SubAccount, None, None]:
        for linked_account in self.linked_accounts:
            for sub_account in linked_account.sub_accounts:
                yield sub_account


@dataclass(frozen=True)
class ScenarioConfig:
    valuation_ccy: CurrencyCode
    start_date: date
    end_date: date


class Scenario(abc.ABC):
    def __init__(
        self,
        config: ScenarioConfig,
    ):
        self.config = config

    @abc.abstractmethod
    def get_initial_state(self) -> SimulationState:
        pass

    @abc.abstractmethod
    def next_state(self, current_date: date, current_state: SimulationState, market: Market) -> SimulationState:
        pass


@dataclass(frozen=True)
class SubAccountSimResult:
    linked_account: LinkedAccount
    sub_account: SubAccount
    items: list[ItemType]


@dataclass(frozen=True)
class LinkedAccountSimResult:
    linked_account: LinkedAccount
    sub_accounts: list[SubAccountSimResult]


@dataclass(frozen=True)
class SimResult:
    current_date: date
    scenario_config: ScenarioConfig
    linked_accounts: list[LinkedAccountSimResult]

    @property
    def current_time(self) -> datetime:
        return datetime.combine(self.current_date, time(hour=18, minute=0), tzinfo=timezone.utc)


class Simulator:
    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.market = Market(
            last_val_date=scenario.config.end_date,
            valuation_ccy=scenario.config.valuation_ccy,
        )

    def run_simulation(self) -> t.Generator[SimResult, None, None]:
        current_date = self.scenario.config.start_date
        current_state = self.scenario.get_initial_state()
        yield self._create_sim_result(current_date, current_state)
        while current_date <= self.scenario.config.end_date:
            for sub_account in current_state.iter_sub_accounts():
                sub_account.sim(
                    current_date=current_date,
                    market=self.market,
                )
            next_state = self.scenario.next_state(
                current_date=current_date,
                current_state=deepcopy(current_state),
                market=self.market,
            )
            yield self._create_sim_result(current_date, next_state)
            current_state = next_state
            current_date += timedelta(days=1)

    def _create_sub_account_sim_result(
        self,
        current_date: date,
        linked_account: LinkedAccount,
        sub_account: SubAccount,
    ) -> SubAccountSimResult:
        return SubAccountSimResult(
            linked_account=linked_account,
            sub_account=sub_account,
            items=sub_account.get_items(
                as_of=current_date,
                market=self.market,
            ),
        )

    def _create_linked_account_sim_result(
        self,
        current_date: date,
        linked_account: LinkedAccount,
    ) -> LinkedAccountSimResult:
        return LinkedAccountSimResult(
            linked_account=linked_account,
            sub_accounts=[
                self._create_sub_account_sim_result(
                    current_date=current_date,
                    linked_account=linked_account,
                    sub_account=sub_account,
                )
                for sub_account in linked_account.sub_accounts
            ],
        )

    def _create_sim_result(
        self,
        current_date: date,
        state: SimulationState,
    ) -> SimResult:
        return SimResult(
            current_date=current_date,
            scenario_config=self.scenario.config,
            linked_accounts=[
                self._create_linked_account_sim_result(
                    current_date=current_date,
                    linked_account=linked_account,
                )
                for linked_account in state.linked_accounts
            ],
        )
