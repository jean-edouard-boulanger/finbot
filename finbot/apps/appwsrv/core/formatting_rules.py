from functools import cache

from finbot.apps.appwsrv.schema import (
    AssetClassFormattingRule,
    AssetTypeClassFormattingRule,
    AssetTypeFormattingRule,
)
from finbot.core.schema import HexColour
from finbot.providers.schema import AssetClass, AssetType

ASSET_CLASSES_FORMATTING_RULES: dict[AssetClass, AssetClassFormattingRule] = {
    AssetClass.equities: AssetClassFormattingRule(
        asset_class=AssetClass.equities,
        pretty_name="Equities",
        dominant_colour=HexColour("#ef233c"),
    ),
    AssetClass.fixed_income: AssetClassFormattingRule(
        asset_class=AssetClass.fixed_income,
        pretty_name="Fixed income",
        dominant_colour=HexColour("#0A9396"),
    ),
    AssetClass.private_debt: AssetClassFormattingRule(
        asset_class=AssetClass.private_debt,
        pretty_name="Private debt",
        dominant_colour=HexColour("#f72585"),
    ),
    AssetClass.currency: AssetClassFormattingRule(
        asset_class=AssetClass.currency,
        pretty_name="Currency",
        dominant_colour=HexColour("#52b788"),
    ),
    AssetClass.foreign_currency: AssetClassFormattingRule(
        asset_class=AssetClass.foreign_currency,
        pretty_name="Foreign currency",
        dominant_colour=HexColour("#07E4A2"),
    ),
    AssetClass.crypto: AssetClassFormattingRule(
        asset_class=AssetClass.crypto,
        pretty_name="Crypto",
        dominant_colour=HexColour("#480ca8"),
    ),
    AssetClass.real_estate: AssetClassFormattingRule(
        asset_class=AssetClass.real_estate,
        pretty_name="Real estate",
        dominant_colour=HexColour("#9B2226"),
    ),
    AssetClass.commodities: AssetClassFormattingRule(
        asset_class=AssetClass.commodities,
        pretty_name="Commodities",
        dominant_colour=HexColour("#ff9f1c"),
    ),
    AssetClass.multi_asset: AssetClassFormattingRule(
        asset_class=AssetClass.multi_asset,
        pretty_name="Multi-asset",
        dominant_colour=HexColour("#2b2d42"),
    ),
}

ASSET_TYPES_FORMATTING_RULES: dict[AssetType, AssetTypeFormattingRule] = {
    AssetType.cash: AssetTypeFormattingRule(
        asset_type=AssetType.cash,
        pretty_name="Cash",
        abbreviated_name="C",
    ),
    AssetType.bond: AssetTypeFormattingRule(
        asset_type=AssetType.bond,
        pretty_name="Bond",
        abbreviated_name="BON",
    ),
    AssetType.stock: AssetTypeFormattingRule(
        asset_type=AssetType.stock,
        pretty_name="Stock",
        abbreviated_name="ST",
    ),
    AssetType.option: AssetTypeFormattingRule(
        asset_type=AssetType.option,
        pretty_name="Option",
        abbreviated_name="OPT",
    ),
    AssetType.future: AssetTypeFormattingRule(
        asset_type=AssetType.future,
        pretty_name="Future",
        abbreviated_name="FUT",
    ),
    AssetType.ETF: AssetTypeFormattingRule(
        asset_type=AssetType.ETF,
        pretty_name="ETF",
        abbreviated_name="ETF",
    ),
    AssetType.ETN: AssetTypeFormattingRule(
        asset_type=AssetType.ETN,
        pretty_name="ETN",
        abbreviated_name="ETN",
    ),
    AssetType.ETC: AssetTypeFormattingRule(
        asset_type=AssetType.ETC,
        pretty_name="ETC",
        abbreviated_name="ETC",
    ),
    AssetType.generic_fund: AssetTypeFormattingRule(
        asset_type=AssetType.generic_fund,
        pretty_name="Generic fund",
        abbreviated_name="F",
    ),
    AssetType.loan: AssetTypeFormattingRule(
        asset_type=AssetType.loan,
        pretty_name="Loan",
        abbreviated_name="LO",
    ),
    AssetType.precious_metal: AssetTypeFormattingRule(
        asset_type=AssetType.precious_metal,
        pretty_name="Precious metal",
        abbreviated_name="MT",
    ),
    AssetType.crypto_currency: AssetTypeFormattingRule(
        asset_type=AssetType.crypto_currency,
        pretty_name="Crypto-currency",
        abbreviated_name="Cx",
    ),
    AssetType.utility_token: AssetTypeFormattingRule(
        asset_type=AssetType.utility_token,
        pretty_name="Utility token",
        abbreviated_name="UTx",
    ),
    AssetType.security_token: AssetTypeFormattingRule(
        asset_type=AssetType.security_token,
        pretty_name="Security token",
        abbreviated_name="STx",
    ),
    AssetType.stable_coin: AssetTypeFormattingRule(
        asset_type=AssetType.stable_coin,
        pretty_name="Stable-coin",
        abbreviated_name="SCx",
    ),
}

ASSETS_VALUATION_COLOUR = "#07E4A2"
ACCOUNTS_PALETTE: list[HexColour] = [
    "#ef233c",
    "#0A9396",
    "#f72585",
    "#52b788",
    "#07E4A2",
    "#480ca8",
    "#9B2226",
    "#ff9f1c",
    "#2b2d42",
]


def get_asset_classes_formatting_rules() -> dict[AssetClass, AssetClassFormattingRule]:
    return ASSET_CLASSES_FORMATTING_RULES


def get_asset_class_formatting_rule(
    asset_class: AssetClass,
) -> AssetClassFormattingRule:
    return get_asset_classes_formatting_rules()[asset_class]


def get_asset_class_formatting_rule_by_name(
    asset_class_name: str,
) -> AssetClassFormattingRule:
    return get_asset_class_formatting_rule(AssetClass[asset_class_name])


def get_asset_types_formatting_rules() -> dict[AssetType, AssetTypeFormattingRule]:
    return ASSET_TYPES_FORMATTING_RULES


def get_asset_type_formatting_rule(asset_type: AssetType) -> AssetTypeFormattingRule:
    return get_asset_types_formatting_rules()[asset_type]


def get_asset_type_formatting_rule_by_name(
    asset_type_name: str,
) -> AssetTypeFormattingRule:
    return get_asset_type_formatting_rule(AssetType[asset_type_name])


@cache
def get_asset_type_class_formatting_rule(
    asset_type: AssetType,
    asset_class: AssetClass,
) -> AssetTypeClassFormattingRule:
    asset_type_fmt = get_asset_type_formatting_rule(asset_type)
    asset_class_fmt = get_asset_class_formatting_rule(asset_class)
    return AssetTypeClassFormattingRule(
        asset_type=asset_type,
        asset_class=asset_class,
        pretty_name=f"{asset_type_fmt.pretty_name} ({asset_class_fmt.pretty_name})",
        dominant_colour=asset_class_fmt.dominant_colour,
    )


def get_asset_type_class_formatting_rule_by_name(
    asset_type_name: str,
    asset_class_name: str,
) -> AssetTypeClassFormattingRule:
    return get_asset_type_class_formatting_rule(
        asset_type=AssetType[asset_type_name],
        asset_class=AssetClass[asset_class_name],
    )
