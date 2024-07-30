import typing as t
from datetime import date

from finbot.core.schema import CurrencyCode
from finbot.providers import schema as providers_schema
from finbot.scripts.demo import fixtures
from finbot.scripts.demo import utils as demo_utils
from finbot.scripts.demo.market import Market
from finbot.scripts.demo.sim import (
    BrokerageAccount,
    CashAmount,
    CheckingAccount,
    LinkedAccount,
    ManualPortfolio,
    SavingsAccount,
    Scenario,
    ScenarioConfig,
    SimulationState,
)


class MainScenario(Scenario):
    def __init__(
        self,
        config: ScenarioConfig,
        monthly_salary: float = 4000.0,
        monthly_rent: float = 800.0,
        monthly_spendings: float = 1000.0,
        pension_contribution_rate: float = 0.08,
        local_ccy: CurrencyCode = CurrencyCode("EUR"),
    ):
        super().__init__(config)
        self.monthly_salary = monthly_salary
        self.monthly_rent = monthly_rent
        self.monthly_spendings = monthly_spendings
        self.pension_contribution_rate = pension_contribution_rate
        self.local_ccy = local_ccy

    def get_initial_state(self) -> SimulationState:
        return SimulationState(
            linked_accounts=[
                LinkedAccount(
                    identifier="bank-account-1",
                    description=fixtures.get_fake_bank_name(),
                    sub_accounts=[
                        CheckingAccount(
                            identifier="checking-1",
                            description=fixtures.get_fake_checking_account_name(),
                            currency=self.local_ccy,
                            balance=1000.0,
                        ),
                        SavingsAccount(
                            identifier="savings-1",
                            description=fixtures.get_fake_savings_account_name(),
                            currency=self.local_ccy,
                            balance=1000.0,
                            yearly_rate=0.03,
                            payment_frequency="monthly",
                        ),
                    ],
                ),
                LinkedAccount(
                    identifier="inv-1",
                    description=fixtures.get_fake_investment_bank_name(),
                    sub_accounts=[
                        BrokerageAccount(
                            account_sub_type="pension",
                            identifier="port-1",
                            description=fixtures.get_fake_pension_fund_name(),
                            currency=self.local_ccy,
                        )
                    ],
                ),
                LinkedAccount(
                    identifier="inv-2",
                    description=fixtures.get_fake_investment_bank_name(),
                    sub_accounts=[
                        BrokerageAccount(
                            account_sub_type="brokerage",
                            identifier="port-1",
                            description="Portfolio",
                            currency=self.local_ccy,
                        )
                    ],
                ),
                LinkedAccount(
                    identifier="crypto-1",
                    description=fixtures.get_fake_crypto_exchange_name(),
                    sub_accounts=[
                        BrokerageAccount(
                            account_sub_type="crypto exchange",
                            identifier="port-1",
                            description="Portfolio",
                            currency=CurrencyCode("USD"),
                        )
                    ],
                ),
                LinkedAccount(
                    identifier="real-estate-1",
                    description="Real Estate",
                    sub_accounts=[
                        ManualPortfolio(
                            identifier="port-1",
                            description="Portfolio",
                            currency=self.local_ccy,
                            type_=providers_schema.AccountType.other,
                            subtype=None,
                            items=[
                                providers_schema.Asset(
                                    name="Apartment (64 boulevard de la Liberation)",
                                    asset_class=providers_schema.AssetClass.real_estate,
                                    asset_type=providers_schema.AssetType.residential_property,
                                    value_in_account_ccy=120_000,
                                    currency=self.local_ccy,
                                )
                            ],
                        )
                    ],
                ),
            ]
        )

    @staticmethod
    def get_checking_account(state: SimulationState) -> CheckingAccount:
        return t.cast(CheckingAccount, state.get_sub_account("bank-account-1", "checking-1"))

    @staticmethod
    def get_savings_account(state: SimulationState) -> SavingsAccount:
        return t.cast(SavingsAccount, state.get_sub_account("bank-account-1", "savings-1"))

    @staticmethod
    def get_pension_account(state: SimulationState) -> BrokerageAccount:
        return t.cast(BrokerageAccount, state.get_sub_account("inv-1", "port-1"))

    @staticmethod
    def get_brokerage_account(state: SimulationState) -> BrokerageAccount:
        return t.cast(BrokerageAccount, state.get_sub_account("inv-2", "port-1"))

    @staticmethod
    def get_crypto_account(state: SimulationState) -> BrokerageAccount:
        return t.cast(BrokerageAccount, state.get_sub_account("crypto-1", "port-1"))

    def next_state(self, current_date: date, current_state: SimulationState, market: Market) -> SimulationState:
        checking_account = self.get_checking_account(current_state)
        if demo_utils.is_last_day_of_year(current_date):
            self.monthly_salary *= 1.08

        if demo_utils.is_last_business_day_of_month(current_date):
            max_emergency_fund_amount = self.monthly_salary * 4
            invested_amount = 0.7 * checking_account.balance
            savings_account = self.get_savings_account(current_state)
            if savings_account.balance < max_emergency_fund_amount:
                checking_account.transfer(invested_amount, savings_account)
            else:
                checking_account.withdraw(invested_amount)
                stocks_alloc = 0.85 * invested_amount
                brokerage_account = self.get_brokerage_account(current_state)
                brokerage_account.deposit_cash(stocks_alloc, checking_account.currency)
                brokerage_account.buy_asset(
                    ticker="SPY",  # SPDR S&P 500 ETF Trust
                    amount=CashAmount(stocks_alloc, checking_account.currency),
                    as_of=current_date,
                    market=market,
                )
                crypto_account = self.get_crypto_account(current_state)
                crypto_alloc = invested_amount - stocks_alloc
                crypto_account.deposit_cash(crypto_alloc, checking_account.currency)
                crypto_account.buy_asset(
                    ticker="BTC-USD",
                    amount=CashAmount(0.495 * crypto_alloc, checking_account.currency),
                    as_of=current_date,
                    market=market,
                )
                crypto_account.buy_asset(
                    ticker="ETH-USD",
                    amount=CashAmount(0.495 * crypto_alloc, checking_account.currency),
                    as_of=current_date,
                    market=market,
                )
            checking_account.deposit(self.monthly_salary)
            if current_date.month == 1:
                # Bonus (20% of yearly salary)
                checking_account.deposit(0.2 * self.monthly_salary * 12)
            if self.pension_contribution_rate > 0.0:
                pension_account = self.get_pension_account(current_state)
                pension_contrib_amount = self.pension_contribution_rate * self.monthly_salary
                pension_account.deposit_cash(
                    amount=pension_contrib_amount,
                    currency=self.local_ccy,
                )
                pension_account.buy_asset(
                    ticker="URTH",  # iShares MSCI World ETF
                    amount=CashAmount(pension_contrib_amount, self.local_ccy),
                    as_of=current_date,
                    market=market,
                )
        if current_date.day == 1:
            checking_account.withdraw(self.monthly_rent)
        checking_account.withdraw(self.monthly_spendings / 30.0)
        return current_state
