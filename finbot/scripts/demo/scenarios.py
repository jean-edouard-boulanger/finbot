import random
import typing as t
from datetime import date

from finbot.core.schema import CurrencyCode
from finbot.providers import schema as providers_schema
from finbot.providers.schema import TransactionType
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


class _Subscription(t.NamedTuple):
    day_of_month: int
    amount: float
    counterparty: str
    description: str
    spending_category_primary: str
    spending_category_detailed: str


SUBSCRIPTIONS: list[_Subscription] = [
    _Subscription(3, 15.99, "Netflix", "Netflix subscription", "ENTERTAINMENT", "ENTERTAINMENT_TV_AND_MOVIES"),
    _Subscription(5, 9.99, "Spotify", "Spotify Premium", "ENTERTAINMENT", "ENTERTAINMENT_MUSIC_AND_AUDIO"),
    _Subscription(8, 25.00, "Mobile Carrier", "Mobile plan", "RENT_AND_UTILITIES", "RENT_AND_UTILITIES_TELEPHONE"),
    _Subscription(
        10, 35.00, "Internet Provider", "Home internet", "RENT_AND_UTILITIES", "RENT_AND_UTILITIES_INTERNET_AND_CABLE"
    ),
    _Subscription(15, 29.99, "FitClub", "Gym membership", "PERSONAL_CARE", "PERSONAL_CARE_GYMS_AND_FITNESS_CENTERS"),
]


GROCERY_MERCHANTS = ["Carrefour", "Monoprix", "Lidl", "Auchan"]
COFFEE_MERCHANTS = ["Starbucks", "Pret a Manger", "Local Coffee"]
RESTAURANT_MERCHANTS = ["Le Bistrot", "Trattoria Roma", "Sushi Place", "Burger House"]
ONLINE_MERCHANTS = ["Amazon", "Zalando", "Asos"]


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
                checking_account.transfer(
                    invested_amount,
                    savings_account,
                    current_date=current_date,
                    description="Emergency fund top-up",
                    out_spending_category_primary="TRANSFER_OUT",
                    out_spending_category_detailed="TRANSFER_OUT_SAVINGS",
                    in_spending_category_primary="TRANSFER_IN",
                    in_spending_category_detailed="TRANSFER_IN_SAVINGS",
                )
            else:
                brokerage_linked = current_state.get_linked_account("inv-2")
                crypto_linked = current_state.get_linked_account("crypto-1")
                stocks_alloc = 0.85 * invested_amount
                crypto_alloc = invested_amount - stocks_alloc
                checking_account.withdraw(
                    stocks_alloc,
                    current_date=current_date,
                    description="Investment funding",
                    transaction_type=TransactionType.transfer_out,
                    counterparty=brokerage_linked.description,
                    spending_category_primary="TRANSFER_OUT",
                    spending_category_detailed="TRANSFER_OUT_INVESTMENT_AND_RETIREMENT_FUNDS",
                )
                checking_account.withdraw(
                    crypto_alloc,
                    current_date=current_date,
                    description="Investment funding",
                    transaction_type=TransactionType.transfer_out,
                    counterparty=crypto_linked.description,
                    spending_category_primary="TRANSFER_OUT",
                    spending_category_detailed="TRANSFER_OUT_INVESTMENT_AND_RETIREMENT_FUNDS",
                )
                brokerage_account = self.get_brokerage_account(current_state)
                brokerage_account.deposit_cash(
                    stocks_alloc,
                    checking_account.currency,
                    current_date=current_date,
                    description="Investment funding",
                    counterparty=checking_account.description,
                    spending_category_primary="TRANSFER_IN",
                    spending_category_detailed="TRANSFER_IN_INVESTMENT_AND_RETIREMENT_FUNDS",
                )
                brokerage_account.buy_asset(
                    ticker="SPY",  # SPDR S&P 500 ETF Trust
                    amount=CashAmount(stocks_alloc, checking_account.currency),
                    as_of=current_date,
                    market=market,
                )
                crypto_account = self.get_crypto_account(current_state)
                crypto_account.deposit_cash(
                    crypto_alloc,
                    checking_account.currency,
                    current_date=current_date,
                    description="Investment funding",
                    counterparty=checking_account.description,
                    spending_category_primary="TRANSFER_IN",
                    spending_category_detailed="TRANSFER_IN_INVESTMENT_AND_RETIREMENT_FUNDS",
                )
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
            checking_account.deposit(
                self.monthly_salary,
                current_date=current_date,
                description="Salary",
                counterparty="Employer",
                spending_category_primary="INCOME",
                spending_category_detailed="INCOME_WAGES",
            )
            if current_date.month == 1:
                # Bonus (20% of yearly salary)
                checking_account.deposit(
                    0.2 * self.monthly_salary * 12,
                    current_date=current_date,
                    description="Annual bonus",
                    counterparty="Employer",
                    spending_category_primary="INCOME",
                    spending_category_detailed="INCOME_WAGES",
                )
            if self.pension_contribution_rate > 0.0:
                pension_account = self.get_pension_account(current_state)
                pension_contrib_amount = self.pension_contribution_rate * self.monthly_salary
                pension_account.deposit_cash(
                    amount=pension_contrib_amount,
                    currency=self.local_ccy,
                    current_date=current_date,
                    description="Pension contribution",
                    transaction_type=TransactionType.contribution,
                    counterparty="Employer",
                    spending_category_primary="TRANSFER_IN",
                    spending_category_detailed="TRANSFER_IN_INVESTMENT_AND_RETIREMENT_FUNDS",
                )
                pension_account.buy_asset(
                    ticker="URTH",  # iShares MSCI World ETF
                    amount=CashAmount(pension_contrib_amount, self.local_ccy),
                    as_of=current_date,
                    market=market,
                )
        if current_date.day == 1:
            checking_account.withdraw(
                self.monthly_rent,
                current_date=current_date,
                description="Monthly rent",
                transaction_type=TransactionType.payment,
                counterparty="Landlord",
                spending_category_primary="RENT_AND_UTILITIES",
                spending_category_detailed="RENT_AND_UTILITIES_RENT",
            )
        self._record_subscriptions(current_date, checking_account)
        self._record_daily_spending(current_date, checking_account)
        return current_state

    @staticmethod
    def _record_subscriptions(current_date: date, checking_account: CheckingAccount) -> None:
        for sub in SUBSCRIPTIONS:
            if current_date.day == sub.day_of_month:
                checking_account.withdraw(
                    sub.amount,
                    current_date=current_date,
                    description=sub.description,
                    transaction_type=TransactionType.payment,
                    counterparty=sub.counterparty,
                    spending_category_primary=sub.spending_category_primary,
                    spending_category_detailed=sub.spending_category_detailed,
                )

    def _record_daily_spending(self, current_date: date, checking_account: CheckingAccount) -> None:
        budget_scale = self.monthly_spendings / 1000.0
        is_weekday = current_date.weekday() < 5
        is_weekend = not is_weekday

        def _spend(
            amount: float,
            description: str,
            counterparty: str,
            primary: str,
            detailed: str,
        ) -> None:
            checking_account.withdraw(
                round(amount * budget_scale, 2),
                current_date=current_date,
                description=description,
                transaction_type=TransactionType.purchase,
                counterparty=counterparty,
                spending_category_primary=primary,
                spending_category_detailed=detailed,
            )

        if current_date.day % 3 == 0:
            _spend(
                random.uniform(35, 60),
                "Groceries",
                random.choice(GROCERY_MERCHANTS),
                "FOOD_AND_DRINK",
                "FOOD_AND_DRINK_GROCERIES",
            )
        if is_weekday and random.random() < 0.6:
            _spend(
                random.uniform(2.5, 5.5),
                "Coffee",
                random.choice(COFFEE_MERCHANTS),
                "FOOD_AND_DRINK",
                "FOOD_AND_DRINK_COFFEE",
            )
        if is_weekday and random.random() < 0.4:
            _spend(
                random.uniform(8, 18),
                "Lunch",
                "Cafeteria",
                "FOOD_AND_DRINK",
                "FOOD_AND_DRINK_FAST_FOOD",
            )
        if is_weekend and random.random() < 0.5:
            _spend(
                random.uniform(25, 70),
                "Restaurant",
                random.choice(RESTAURANT_MERCHANTS),
                "FOOD_AND_DRINK",
                "FOOD_AND_DRINK_RESTAURANT",
            )
        if is_weekday:
            _spend(
                random.uniform(2, 4) * 2,
                "Public transit",
                "Transit Authority",
                "TRANSPORTATION",
                "TRANSPORTATION_PUBLIC_TRANSIT",
            )
        if random.random() < 0.05:
            _spend(
                random.uniform(12, 35),
                "Ride share",
                "Uber",
                "TRANSPORTATION",
                "TRANSPORTATION_TAXIS_AND_RIDE_SHARES",
            )
        if current_date.weekday() == 5 and random.random() < 0.3:
            _spend(
                random.uniform(40, 150),
                "Online purchase",
                random.choice(ONLINE_MERCHANTS),
                "GENERAL_MERCHANDISE",
                "GENERAL_MERCHANDISE_ONLINE_MARKETPLACES",
            )
