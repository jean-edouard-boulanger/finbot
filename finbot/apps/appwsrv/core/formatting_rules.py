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
    AssetType.commercial_property: AssetTypeFormattingRule(
        asset_type=AssetType.commercial_property,
        pretty_name="Commercial property",
        abbreviated_name="CP",
    ),
    AssetType.residential_property: AssetTypeFormattingRule(
        asset_type=AssetType.residential_property,
        pretty_name="Residential property",
        abbreviated_name="RP",
    ),
    AssetType.land_property: AssetTypeFormattingRule(
        asset_type=AssetType.land_property,
        pretty_name="Land property",
        abbreviated_name="LP",
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


UNKNOWN_CURRENCY_COLOR = "#393939"
CRYPTOCURRENCY_COLOR = ASSET_CLASSES_FORMATTING_RULES[AssetClass.crypto].dominant_colour
CURRENCIES_COLORS = {
    "AED": "#C05D6D",
    "AFN": "#C96E56",
    "ALL": "#835CBF",
    "AMD": "#7365BA",
    "ANG": "#D19D5A",
    "AOA": "#9D70BA",
    "ARS": "#C4985F",
    "AUD": "#C5AC76",
    "AWG": "#B85969",
    "AZN": "#D5B95C",
    "BAM": "#C0535A",
    "BBD": "#A7A364",
    "BDT": "#B775C2",
    "BGN": "#C4B55F",
    "BHD": "#C27869",
    "BIF": "#B84F8E",
    "BMD": "#73B56D",
    "BND": "#B0985F",
    "BOB": "#C4945F",
    "BRL": "#5ED5DA",
    "BSD": "#B26F6B",
    "BTN": "#B49D57",
    "BWP": "#9356B1",
    "BYN": "#A2C476",
    "BZD": "#A67C64",
    "CAD": "#87A85B",
    "CDF": "#5FC674",
    "CHF": "#AA5C63",
    "CLP": "#6B9AC6",
    "CNY": "#AF5458",
    "COP": "#69C2B1",
    "CRC": "#53C286",
    "CUP": "#4F8FB7",
    "CVE": "#DAAF5E",
    "CZK": "#BB8D70",
    "DJF": "#B56D96",
    "DKK": "#BB8A50",
    "DOP": "#D58F5C",
    "DZD": "#68C1AE",
    "EGP": "#B5886D",
    "ERN": "#C4A676",
    "ETB": "#87B56D",
    "EUR": "#65C0D0",
    "FJD": "#C98056",
    "FKP": "#B48157",
    "GBP": "#AC6ECD",
    "GEL": "#CB62C6",
    "GGP": "#CC7E63",
    "GHS": "#589DB7",
    "GIP": "#CD846E",
    "GMD": "#C68F6B",
    "GNF": "#5FB2DC",
    "GTQ": "#6A8DB0",
    "GYD": "#72D85D",
    "HKD": "#BE7D67",
    "HNL": "#D35B9C",
    "HRK": "#C69377",
    "HTG": "#716CC7",
    "HUF": "#B95A60",
    "IDR": "#B87A6F",
    "ILS": "#B7A863",
    "INR": "#BC71B7",
    "IQD": "#CA786D",
    "IRR": "#97AE69",
    "ISK": "#B4C476",
    "JMD": "#6DBF5C",
    "JOD": "#67A1AB",
    "JPY": "#CEAE6F",
    "KES": "#C4925F",
    "KGS": "#5EAAC3",
    "KHR": "#66A97F",
    "KMF": "#CEA76F",
    "KPW": "#BA7F65",
    "KRW": "#B8A063",
    "KWD": "#C88661",
    "KYD": "#CA9D6D",
    "KZT": "#627BB5",
    "LAK": "#A1C35E",
    "LBP": "#A48263",
    "LKR": "#C5A36A",
    "LRD": "#73AC67",
    "LSL": "#B07D55",
    "LYD": "#C69E55",
    "MAD": "#677AD6",
    "MDL": "#A28461",
    "MGA": "#BBA850",
    "MKD": "#D37F66",
    "MMK": "#6BAFC6",
    "MNT": "#BDCE6F",
    "MRU": "#70BBB2",
    "MUR": "#CEAA63",
    "MVR": "#B7824F",
    "MWK": "#C1A968",
    "MXN": "#B95A5A",
    "MYR": "#8C64A6",
    "MZN": "#95BE5C",
    "NAD": "#BC5651",
    "NGN": "#C28069",
    "NIO": "#64A671",
    "NOK": "#5C88AA",
    "NPR": "#BB8B70",
    "NZD": "#7556C9",
    "OMR": "#AE9B69",
    "PEN": "#5ABB70",
    "PGK": "#ABC555",
    "PHP": "#5FC6C6",
    "PKR": "#6188B4",
    "PLN": "#94B859",
    "PYG": "#61CA75",
    "QAR": "#A87D65",
    "RON": "#7092BA",
    "RSD": "#DEB45F",
    "RUB": "#5B88D4",
    "RWF": "#C4768F",
    "SAR": "#B87D63",
    "SBD": "#BE8F5C",
    "SCR": "#B39D6C",
    "SDG": "#9B6AC5",
    "SEK": "#6ECC63",
    "SGD": "#65BCB2",
    "SHP": "#AC8A67",
    "SLL": "#62B156",
    "SOS": "#B7816E",
    "SRD": "#C3AA5E",
    "SSP": "#63B0CC",
    "STD": "#D0596C",
    "SYP": "#A56EB7",
    "SZL": "#6EC269",
    "THB": "#C98B6C",
    "TJS": "#B5C956",
    "TMT": "#5EAEC3",
    "TND": "#5EAF70",
    "TOP": "#BED366",
    "TRY": "#BB508A",
    "TTD": "#6889AD",
    "TWD": "#6D9AB5",
    "TZS": "#AC5D67",
    "UAH": "#62A39F",
    "UGX": "#D0A765",
    "USD": "#BDD059",
    "UYU": "#A79D64",
    "UZS": "#C28975",
    "VES": "#A99666",
    "VND": "#C4D85D",
    "VUV": "#61CA8F",
    "WST": "#6973C2",
    "XAF": "#C45F95",
    "XCD": "#C07C5D",
    "XOF": "#B376C4",
    "XPF": "#C6A277",
    "YER": "#B2C275",
    "ZAR": "#A47A63",
    "ZMW": "#A2AA5C",
}


def get_currency_color(currency_code: str | None) -> HexColour:
    if not currency_code:
        return UNKNOWN_CURRENCY_COLOR
    return CURRENCIES_COLORS.get(currency_code, UNKNOWN_CURRENCY_COLOR)


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
