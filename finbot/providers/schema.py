import enum
from typing import Any, Self, TypeAlias

from finbot.core.pydantic_ import Field, root_validator
from finbot.core.schema import BaseModel, CurrencyCode

ProviderSpecificPayloadType: TypeAlias = dict[str, str | int | float | bool]
SchemaNamespace = "Providers"


DEPOSITORY_ACCOUNT_SUB_TYPES = (
    "checking",
    "savings",
    "hsa",
    "cd",
    "money market",
    "paypal",
    "prepaid",
    "cash management",
    "ebt",
    "other",
)

CREDIT_ACCOUNT_SUB_TYPES = ("credit card", "paypal", "other")

LOAN_ACCOUNT_SUB_TYPES = (
    "auto",
    "business",
    "commercial",
    "construction",
    "consumer",
    "home equity",
    "loan",
    "mortgage",
    "overdraft",
    "line of credit",
    "student",
    "other",
)

INVESTMENT_ACCOUNT_SUB_TYPES = (
    "529",
    "401a",
    "401k",
    "403B",
    "457b",
    "brokerage",
    "cash isa",
    "crypto exchange",
    "education savings account",
    "fixed annuity",
    "gic",
    "health reimbursement arrangement",
    "hsa",
    "ira",
    "isa",
    "keogh",
    "lif",
    "life insurance",
    "lira",
    "lrif",
    "lrsp",
    "mutual fund",
    "non-custodial wallet",
    "non-taxable brokerage account",
    "other",
    "other annuity",
    "other insurance",
    "pension",
    "prif",
    "profit sharing plan",
    "qshr",
    "rdsp",
    "resp",
    "retirement",
    "rlif",
    "roth",
    "roth 401k",
    "rrif",
    "rrsp",
    "sarsep",
    "sep ira",
    "simple ira",
    "sipp",
    "stock plan",
    "tfsa",
    "trust",
    "ugma",
    "utma",
    "variable annuity",
)


class AssetClass(str, enum.Enum):
    equities = "equities"
    fixed_income = "fixed_income"
    private_debt = "private_debt"
    currency = "currency"
    foreign_currency = "foreign_currency"
    crypto = "crypto"
    real_estate = "real_estate"
    commodities = "commodities"
    multi_asset = "multi_asset"


class AssetType(str, enum.Enum):
    cash = "cash"
    bond = "bond"
    stock = "stock"
    option = "option"
    future = "future"
    ETF = "ETF"
    ETN = "ETN"
    ETC = "ETC"
    generic_fund = "generic_fund"
    loan = "loan"
    precious_metal = "precious_metal"
    crypto_currency = "crypto_currency"
    utility_token = "utility_token"
    security_token = "security_token"
    stable_coin = "stable_coin"


class AccountType(str, enum.Enum):
    depository = "depository"
    credit = "credit"
    loan = "loan"
    investment = "investment"
    other = "other"


class Account(BaseModel):
    id: str = Field(description="Account identifier (unique across all accounts in this linked account)")
    name: str = Field(description="Account name/description")
    iso_currency: CurrencyCode = Field(description="Account currency")
    type: AccountType = Field(description="Account type")
    sub_type: str | None = Field(description="Account sub-type")

    @root_validator
    def validate_sub_type(cls, values: Any) -> Any:
        allowed_sub_types = {
            AccountType.depository: DEPOSITORY_ACCOUNT_SUB_TYPES,
            AccountType.credit: CREDIT_ACCOUNT_SUB_TYPES,
            AccountType.investment: INVESTMENT_ACCOUNT_SUB_TYPES,
            AccountType.loan: LOAN_ACCOUNT_SUB_TYPES,
            AccountType.other: (None,),
        }
        account_type, account_sub_type = values.get("type"), values.get("sub_type")
        if account_type is not None and account_sub_type not in allowed_sub_types[account_type]:
            raise ValueError(f"'{account_sub_type}' is not a valid '{account_type.value}' account sub-type")
        return values


class Asset(BaseModel):
    name: str = Field(description="Asset name/description")
    type: str = Field(default_factory=str)  # deprecated
    asset_class: AssetClass = Field(description="Asset class")
    asset_type: AssetType = Field(description="Asset type")
    value_in_account_ccy: float | None = Field(
        default=None,
        description="Asset value expressed in the holding account currency"
        " (mutually exclusive with `value_in_item_ccy`)",
    )
    value_in_item_ccy: float | None = Field(
        default=None,
        description="Asset value expressed in the specified asset currency"
        " (mutually exclusive with `value_in_account_ccy`)",
    )
    units: float | None = Field(default=None, description="Number of asset units held in the account")
    currency: CurrencyCode = Field(description="Asset currency")
    provider_specific: ProviderSpecificPayloadType | None = Field(
        default=None,
        description="Arbitrary data (key/value pair) specific to the provider/asset",
    )

    @root_validator
    def validate_value_and_currency(cls, values: Any) -> Any:
        _validate_value_and_currency(
            value_in_account_ccy=values.get("value_in_account_ccy"),
            value_in_item_ccy=values.get("value_in_item_ccy"),
            currency=values.get("currency"),
        )
        return values

    @classmethod
    def cash(
        cls,
        currency: CurrencyCode,
        is_domestic: bool,
        amount: float,
        provider_specific: ProviderSpecificPayloadType | None = None,
    ) -> Self:
        return cls(
            name=f"{currency}",
            type="currency",  # deprecated
            asset_class=(AssetClass.currency if is_domestic else AssetClass.foreign_currency),
            asset_type=AssetType.cash,
            value_in_item_ccy=amount,
            units=None,
            currency=currency,
            provider_specific=provider_specific,
        )


class AssetsEntry(BaseModel):
    account_id: str = Field(description="Identifier of the account holding the assets")
    items: list[Asset] = Field(description="Assets held in the account")


class Assets(BaseModel):
    accounts: list[AssetsEntry]


class Liability(BaseModel):
    name: str = Field(description="Liability name/description")
    type: str = Field(description="Liability type (credit, loan, etc.)")  # TODO: constrain this with an enum
    value_in_account_ccy: float | None = Field(
        default=None,
        description="Liability amount expressed in the holding account currency"
        " (mutually exclusive with `value_in_item_ccy`)",
    )
    value_in_item_ccy: float | None = Field(
        default=None,
        description="Liability amount expressed in the specified liability currency"
        " (mutually exclusive with `value_in_account_ccy`)",
    )
    currency: CurrencyCode = Field(description="Liability currency")
    provider_specific: ProviderSpecificPayloadType | None = Field(
        default=None,
        description="Arbitrary data (key/value pair) specific to the provider/asset",
    )

    @root_validator
    def validate_value_and_currency(cls, values: Any) -> Any:
        _validate_value_and_currency(
            value_in_account_ccy=values.get("value_in_account_ccy"),
            value_in_item_ccy=values.get("value_in_item_ccy"),
            currency=values.get("currency"),
        )
        return values


class LiabilitiesEntry(BaseModel):
    account_id: str = Field(description="Identifier of the account holding the liabilities")
    items: list[Liability] = Field(description="Liabilities held in the account")


class Liabilities(BaseModel):
    accounts: list[LiabilitiesEntry]


ItemType: TypeAlias = Asset | Liability


def _validate_value_and_currency(
    value_in_account_ccy: float | None,
    value_in_item_ccy: float | None,
    currency: CurrencyCode | None,
) -> None:
    if (value_in_item_ccy is not None and value_in_account_ccy is not None) or (
        value_in_item_ccy is None and value_in_account_ccy is None
    ):
        raise ValueError(
            f"Either `value_in_account_ccy` (={value_in_account_ccy})"
            f" or `value_in_unit_ccy` (={value_in_item_ccy}) must be set"
        )
    if value_in_item_ccy is not None and currency is None:
        raise ValueError(f"`currency` must be set when `value_in_unit_ccy` (={value_in_item_ccy}) is set")
