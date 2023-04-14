from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ParseError as XMLParseError
from xml.etree.ElementTree import fromstring as parse_xml_payload
from xml.etree.ElementTree import parse as parse_xml_file


class FlexReportParserError(Exception):
    pass


@dataclass(frozen=True)
class MTMPerformanceSummaryUnderlying:
    asset_category: str
    sub_category: str
    symbol: str
    description: str
    security_id: str
    security_id_type: str
    cusip: str
    isin: str
    listing_exchange: str
    close_quantity: float
    close_price: float
    commissions: float

    @property
    def full_security_id(self) -> str:
        return _make_full_security_id(self)


@dataclass(frozen=True)
class MTMPerformanceSummaryInBase:
    entries: list[MTMPerformanceSummaryUnderlying]


@dataclass(frozen=True)
class SecurityInfo:
    currency: str
    asset_category: str
    sub_category: str
    symbol: str
    description: str
    security_id: str
    security_id_type: str
    listing_exchange: str

    @property
    def full_security_id(self) -> str:
        return _make_full_security_id(self)


@dataclass(frozen=True)
class SecuritiesInfo:
    entries: list[SecurityInfo]


@dataclass(frozen=True)
class ConversionRate:
    from_ccy: str
    to_ccy: str
    rate: float


@dataclass(frozen=True)
class ConversionRates:
    entries: list[ConversionRate]


@dataclass(frozen=True)
class AccountInformation:
    account_id: str
    alias: str
    currency: str


@dataclass(frozen=True)
class FlexStatementEntries:
    account_information: AccountInformation | None = None
    mtm_performance_summary_in_base: MTMPerformanceSummaryInBase | None = None
    securities_info: SecuritiesInfo | None = None
    conversion_rates: ConversionRates | None = None


FlexStatementEntryType = (
    AccountInformation | MTMPerformanceSummaryInBase | SecuritiesInfo | ConversionRates
)


@dataclass(frozen=True)
class FlexStatement:
    account_id: str
    from_date: date
    to_date: date
    period: str
    entries: FlexStatementEntries


@dataclass(frozen=True)
class FlexReport:
    query_name: str
    statements: list[FlexStatement]


def _make_full_security_id(
    entry: MTMPerformanceSummaryUnderlying | SecurityInfo,
) -> str:
    return f"{entry.asset_category}:{entry.security_id_type}:{entry.security_id}"


def _parse_mtm_performance_summary_underlying(
    node: Element,
) -> MTMPerformanceSummaryUnderlying:
    return MTMPerformanceSummaryUnderlying(
        asset_category=node.attrib["assetCategory"],
        sub_category=node.attrib["subCategory"],
        symbol=node.attrib["symbol"],
        description=node.attrib["description"],
        security_id=node.attrib["securityID"],
        security_id_type=node.attrib["securityIDType"],
        cusip=node.attrib["cusip"],
        isin=node.attrib["isin"],
        listing_exchange=node.attrib["listingExchange"],
        close_quantity=float(node.attrib["closeQuantity"]),
        close_price=float(node.attrib["closePrice"]),
        commissions=float(node.attrib["commissions"]),
    )


def _parse_mtm_performance_summary_in_base(
    node: Element,
) -> MTMPerformanceSummaryInBase:
    return MTMPerformanceSummaryInBase(
        entries=[
            _parse_mtm_performance_summary_underlying(underlying_node)
            for underlying_node in list(node)
            if underlying_node.attrib["symbol"] != ""
        ]
    )


def _parse_account_information(node: Element) -> AccountInformation:
    return AccountInformation(
        account_id=node.attrib["accountId"],
        alias=node.attrib["acctAlias"],
        currency=node.attrib["currency"],
    )


def _parse_security_info(node: Element) -> SecurityInfo:
    return SecurityInfo(
        currency=node.attrib["currency"],
        asset_category=node.attrib["assetCategory"],
        sub_category=node.attrib["subCategory"],
        symbol=node.attrib["symbol"],
        description=node.attrib["description"],
        security_id=node.attrib["securityID"],
        security_id_type=node.attrib["securityIDType"],
        listing_exchange=node.attrib["listingExchange"],
    )


def _parse_securities_info(node: Element) -> SecuritiesInfo:
    return SecuritiesInfo(
        entries=[_parse_security_info(security_node) for security_node in list(node)]
    )


def _parse_conversion_rate(node: Element) -> ConversionRate:
    return ConversionRate(
        from_ccy=node.attrib["fromCurrency"],
        to_ccy=node.attrib["toCurrency"],
        rate=float(node.attrib["rate"]),
    )


def _parse_conversion_rates(node: Element) -> ConversionRates:
    return ConversionRates(
        entries=[_parse_conversion_rate(rate_node) for rate_node in list(node)]
    )


def _parse_flex_statement_entries(nodes: list[Element]) -> FlexStatementEntries:
    account_information: AccountInformation | None = None
    mtm_performance_summary_in_base: MTMPerformanceSummaryInBase | None = None
    securities_info: SecuritiesInfo | None = None
    conversion_rates: ConversionRates | None = None
    for node in nodes:
        node_type = node.tag
        if node_type == "AccountInformation":
            account_information = _parse_account_information(node)
        elif node_type == "MTMPerformanceSummaryInBase":
            mtm_performance_summary_in_base = _parse_mtm_performance_summary_in_base(
                node
            )
        elif node_type == "SecuritiesInfo":
            securities_info = _parse_securities_info(node)
        elif node_type == "ConversionRates":
            conversion_rates = _parse_conversion_rates(node)
    return FlexStatementEntries(
        account_information=account_information,
        mtm_performance_summary_in_base=mtm_performance_summary_in_base,
        securities_info=securities_info,
        conversion_rates=conversion_rates,
    )


def _parse_flex_statement(node: Element) -> FlexStatement:
    return FlexStatement(
        account_id=node.attrib["accountId"],
        from_date=date.fromisoformat(node.attrib["fromDate"]),
        to_date=date.fromisoformat(node.attrib["toDate"]),
        period=node.attrib["period"],
        entries=_parse_flex_statement_entries(list(node)),
    )


def _parse_flex_report(report_root: Element) -> FlexReport:
    try:
        assert report_root is not None
        assert report_root.tag == "FlexQueryResponse"
        flex_statements_node: Element = list(report_root)[0]
        return FlexReport(
            query_name=report_root.attrib["queryName"],
            statements=[
                _parse_flex_statement(flex_statement_node)
                for flex_statement_node in list(flex_statements_node)
            ],
        )
    except Exception as e:
        raise FlexReportParserError(f"while extracting Flex report content: {e}") from e


def parse_flex_report_payload(xml_payload: str) -> FlexReport:
    try:
        return _parse_flex_report(parse_xml_payload(xml_payload))
    except XMLParseError as e:
        raise FlexReportParserError(f"while parsing XML Flex report: {e}") from e


def parse_flex_report_file(report_file_path: Path) -> FlexReport:
    try:
        tree = parse_xml_file(str(report_file_path.expanduser().absolute()))
        return _parse_flex_report(tree.getroot())
    except XMLParseError as e:
        raise FlexReportParserError(f"while parsing XML Flex report: {e}") from e
