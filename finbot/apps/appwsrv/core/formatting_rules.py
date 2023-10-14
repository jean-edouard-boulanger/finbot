from finbot.apps.appwsrv.schema import (
    AssetClassFormattingRule,
    AssetTypeFormattingRule,
    FormattingRules,
)
from finbot.core.schema import HexColour
from finbot.providers.schema import AssetClass, AssetType

ASSET_CLASSES_FORMATTING_RULES: dict[AssetClass, AssetClassFormattingRule] = {
    AssetClass.equities: AssetClassFormattingRule(
        asset_class=AssetClass.equities,
        pretty_name="Equities",
        dominant_colour=HexColour("#DB073D"),
    ),
    AssetClass.fixed_income: AssetClassFormattingRule(
        asset_class=AssetClass.fixed_income,
        pretty_name="Fixed income",
        dominant_colour=HexColour("#073DDB"),
    ),
    AssetClass.private_debt: AssetClassFormattingRule(
        asset_class=AssetClass.private_debt,
        pretty_name="Private debt",
        dominant_colour=HexColour("#DBA507"),
    ),
    AssetClass.currency: AssetClassFormattingRule(
        asset_class=AssetClass.currency,
        pretty_name="Currency",
        dominant_colour=HexColour("#50C47D"),
    ),
    AssetClass.foreign_currency: AssetClassFormattingRule(
        asset_class=AssetClass.foreign_currency,
        pretty_name="Foreign currency",
        dominant_colour=HexColour("#2E8A52"),
    ),
    AssetClass.crypto: AssetClassFormattingRule(
        asset_class=AssetClass.crypto,
        pretty_name="Crypto",
        dominant_colour=HexColour("#5B1355"),
    ),
    AssetClass.real_estate: AssetClassFormattingRule(
        asset_class=AssetClass.real_estate,
        pretty_name="Real estate",
        dominant_colour=HexColour("#3E0C65"),
    ),
    AssetClass.commodities: AssetClassFormattingRule(
        asset_class=AssetClass.commodities,
        pretty_name="Commodities",
        dominant_colour=HexColour("#373737"),
    ),
    AssetClass.multi_asset: AssetClassFormattingRule(
        asset_class=AssetClass.multi_asset,
        pretty_name="Multi-asset",
        dominant_colour=HexColour("#0B5852"),
    ),
}

ASSET_TYPES_FORMATTING_RULES: dict[AssetType, AssetTypeFormattingRule] = {
    AssetType.cash: AssetTypeFormattingRule(
        asset_type=AssetType.cash, pretty_name="Cash", abbreviated_name="C"
    ),
    AssetType.bond: AssetTypeFormattingRule(
        asset_type=AssetType.bond, pretty_name="Bond", abbreviated_name="BON"
    ),
    AssetType.stock: AssetTypeFormattingRule(
        asset_type=AssetType.stock, pretty_name="Stock", abbreviated_name="ST"
    ),
    AssetType.option: AssetTypeFormattingRule(
        asset_type=AssetType.option, pretty_name="Option", abbreviated_name="OPT"
    ),
    AssetType.future: AssetTypeFormattingRule(
        asset_type=AssetType.future, pretty_name="Future", abbreviated_name="FUT"
    ),
    AssetType.ETF: AssetTypeFormattingRule(
        asset_type=AssetType.ETF, pretty_name="ETF", abbreviated_name="ETF"
    ),
    AssetType.ETN: AssetTypeFormattingRule(
        asset_type=AssetType.ETN, pretty_name="ETN", abbreviated_name="ETN"
    ),
    AssetType.generic_fund: AssetTypeFormattingRule(
        asset_type=AssetType.generic_fund,
        pretty_name="Generic fund",
        abbreviated_name="F",
    ),
    AssetType.loan: AssetTypeFormattingRule(
        asset_type=AssetType.loan, pretty_name="Loan", abbreviated_name="LO"
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


def get_asset_classes_formatting_rules() -> dict[AssetClass, AssetClassFormattingRule]:
    return ASSET_CLASSES_FORMATTING_RULES


def get_asset_class_formatting_rule(
    asset_class: AssetClass,
) -> AssetClassFormattingRule:
    return get_asset_classes_formatting_rules()[asset_class]


def get_asset_class_formatting_rule_by_name(
    raw_asset_class: str,
) -> AssetClassFormattingRule | None:
    try:
        asset_class = AssetClass[raw_asset_class]
        return get_asset_class_formatting_rule(asset_class)
    except (ValueError, KeyError):
        return None


def get_asset_types_formatting_rules() -> dict[AssetType, AssetTypeFormattingRule]:
    return ASSET_TYPES_FORMATTING_RULES


def get_asset_type_formatting_rule(asset_type: AssetType) -> AssetTypeFormattingRule:
    return get_asset_types_formatting_rules()[asset_type]


def get_asset_types_formatting_rule_by_name(
    raw_asset_type: str,
) -> AssetTypeFormattingRule | None:
    try:
        asset_type = AssetType[raw_asset_type]
        return get_asset_type_formatting_rule(asset_type)
    except (ValueError, KeyError):
        return None


def get_formatting_rules() -> FormattingRules:
    return FormattingRules(
        asset_classes=list(get_asset_classes_formatting_rules().values()),
        asset_types=list(get_asset_types_formatting_rules().values()),
    )
