from functools import cache

from finbot.apps.appwsrv.schema import (
    AssetClassFormattingRule,
    AssetTypeClassFormattingRule,
    AssetTypeFormattingRule,
)
from finbot.core.crypto_market import is_cryptocurrency_code
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


CURRENCIES_COLORS = {
    "IRR": "#AAB29A",
    "GNF": "#AFCBD9",
    "GIP": "#D5A495",
    "KRW": "#C3AB6D",
    "ILS": "#F5EDC8",
    "HNL": "#E3CDD9",
    "QAR": "#D3CAC5",
    "NPR": "#D1C8C3",
    "GMD": "#DAC8BC",
    "TMT": "#A8CAD3",
    "OMR": "#C8C1AF",
    "BDT": "#968A98",
    "SEK": "#C0D1BE",
    "LRD": "#8FA68A",
    "KES": "#E8D8C8",
    "UYU": "#DCD7B9",
    "KMF": "#E7B368",
    "IQD": "#CEA7A2",
    "GEL": "#D9C3D8",
    "MYR": "#DFD1E8",
    "BGN": "#E6E3D2",
    "BSD": "#D7B9B7",
    "BOB": "#DEC6AC",
    "KPW": "#D6C2B9",
    "NAD": "#CDB9B8",
    "MNT": "#C6C9B8",
    "UAH": "#D1E1E0",
    "SDG": "#BCA7CE",
    "CVE": "#E0D2B7",
    "AZN": "#E6DAB2",
    "SSP": "#BAC2C5",
    "SGD": "#D1DAD9",
    "CUP": "#CCD1D4",
    "UGX": "#E1AE5D",
    "SCR": "#E1BD6F",
    "GGP": "#E2BCAF",
    "BND": "#AAA7A0",
    "BZD": "#CFB9AC",
    "GHS": "#BBC3C6",
    "MAD": "#CDCED3",
    "NOK": "#7EABCC",
    "BIF": "#DAC6D2",
    "TZS": "#F3B2BA",
    "SRD": "#DBD7CB",
    "LBP": "#ECD7C4",
    "CAD": "#B0CD8A",
    "IDR": "#D09E95",
    "PKR": "#CCD3DB",
    "USD": "#BEC49E",
    "AFN": "#EED0C8",
    "INR": "#EDBEEA",
    "FKP": "#B0A093",
    "PLN": "#C4CCB7",
    "TND": "#C8DACC",
    "HKD": "#DEC0B6",
    "ZMW": "#CFD2B3",
    "DZD": "#D7EAE6",
    "RSD": "#CAC9C7",
    "MWK": "#E4CE92",
    "EGP": "#C9BCB4",
    "KGS": "#7B8A8F",
    "DKK": "#C5BBAF",
    "AUD": "#C6B796",
    "SLL": "#B4C7B1",
    "MKD": "#C88F7E",
    "LKR": "#C7AB7C",
    "KHR": "#A0B0A6",
    "TOP": "#D0DAA5",
    "GTQ": "#96ACC1",
    "BAM": "#E4C6C8",
    "SBD": "#DDC2A4",
    "SYP": "#AE9CB4",
    "LSL": "#D5B398",
    "GYD": "#83AA7B",
    "BMD": "#B5BFB4",
    "YER": "#B7BE9C",
    "STD": "#EBD2D6",
    "JOD": "#8BA4A8",
    "XPF": "#F0DFCB",
    "GBP": "#D4C5DC",
    "NZD": "#9E9BA6",
    "VUV": "#7EB596",
    "CLP": "#B2C8DD",
    "VND": "#BDBEB8",
    "MXN": "#D9D3D3",
    "HUF": "#DCBFC1",
    "AOA": "#9B93A0",
    "MRU": "#939C9B",
    "RWF": "#4F4347",
    "TRY": "#E3D6DD",
    "KWD": "#D8CFCA",
    "XOF": "#C7B8CB",
    "SOS": "#D7C3BC",
    "CHF": "#D3888F",
    "BRL": "#B4CECF",
    "COP": "#BACAC7",
    "PHP": "#BDC9C9",
    "BHD": "#ACA2A0",
    "JMD": "#C4C9C3",
    "HRK": "#DBC9BF",
    "SHP": "#D9C9B9",
    "MMK": "#B7C6CB",
    "TWD": "#9EAFB9",
    "AED": "#CDC1C3",
    "HTG": "#C6C5D5",
    "NGN": "#CAB6AF",
    "CRC": "#D2EADD",
    "ISK": "#C9CAC5",
    "TJS": "#DBDECD",
    "LAK": "#D2D5CC",
    "MUR": "#CAC9C7",
    "AWG": "#E2C5CA",
    "CDF": "#8CAA92",
    "EUR": "#BFCACC",
    "MGA": "#E0D7AE",
    "VES": "#DBD0B4",
    "THB": "#BB9F91",
    "ETB": "#9CB190",
    "TTD": "#96B7DA",
    "PYG": "#BFCFC2",
    "WST": "#7A80B0",
    "CNY": "#F9CBCD",
    "ALL": "#C7C0D2",
    "PEN": "#BECBC1",
    "KZT": "#8898BC",
    "JPY": "#CFBD99",
    "ARS": "#F3D2A7",
    "PGK": "#AFB59B",
    "RUB": "#C4CDDC",
    "CZK": "#CCB1A0",
    "DJF": "#BC85A5",
    "AMD": "#B0AFB5",
    "BBD": "#C9C8B6",
    "BWP": "#9F9DA0",
    "LYD": "#F3E7D1",
    "DOP": "#D8B8A1",
    "SZL": "#C7D8C6",
    "NIO": "#96C29F",
    "BTN": "#E8D088",
    "SAR": "#D5C1B8",
    "KYD": "#B9A896",
    "UZS": "#D5B5AA",
    "XCD": "#CD9B84",
    "BYN": "#99AB81",
    "ERN": "#BEB6A9",
    "RON": "#A9B0B8",
    "MZN": "#C1CBB3",
    "FJD": "#E6AB89",
    "XAF": "#CDC0C7",
    "ZAR": "#DB8A5D",
    "ANG": "#CFAE83",
    "MVR": "#EDBB8A",
    "MDL": "#DED2C4"
}


def get_currency_color(currency_code: str) -> HexColour | None:
    if is_cryptocurrency_code(currency_code):
        return get_asset_class_formatting_rule(AssetClass.crypto).dominant_colour
    return CURRENCIES_COLORS.get(currency_code)


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
