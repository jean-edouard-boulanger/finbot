from datetime import date, datetime
from pathlib import Path
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ParseError as XMLParseError
from xml.etree.ElementTree import fromstring as parse_xml_payload
from xml.etree.ElementTree import parse as parse_xml_file

from finbot.core.schema import CurrencyCode
from finbot.providers.interactive_brokers_uk.flex_report import schema


class FlexReportParserError(Exception):
    pass


def _parse_mtm_performance_summary_underlying(
    node: Element,
) -> schema.MTMPerformanceSummaryUnderlying:
    return schema.MTMPerformanceSummaryUnderlying(
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
        report_date=datetime.strptime(node.attrib["reportDate"], "%Y-%m-%d").date(),
    )


def _parse_mtm_performance_summary_in_base(
    node: Element,
) -> schema.MTMPerformanceSummaryInBase:
    return schema.MTMPerformanceSummaryInBase(
        entries=[
            _parse_mtm_performance_summary_underlying(underlying_node)
            for underlying_node in list(node)
            if underlying_node.attrib["symbol"] != ""
        ]
    )


def _parse_account_information(node: Element) -> schema.AccountInformation:
    return schema.AccountInformation(
        account_id=node.attrib["accountId"],
        alias=node.attrib["acctAlias"],
        currency=CurrencyCode.validate(node.attrib["currency"]),
    )


def _parse_security_info(node: Element) -> schema.SecurityInfo:
    return schema.SecurityInfo(
        currency=CurrencyCode.validate(node.attrib["currency"]),
        asset_category=node.attrib["assetCategory"],
        sub_category=node.attrib["subCategory"],
        symbol=node.attrib["symbol"],
        description=node.attrib["description"],
        security_id=node.attrib["securityID"],
        security_id_type=node.attrib["securityIDType"],
        listing_exchange=node.attrib["listingExchange"],
    )


def _parse_securities_info(node: Element) -> schema.SecuritiesInfo:
    return schema.SecuritiesInfo(
        entries=[_parse_security_info(security_node) for security_node in list(node)],
    )


def _parse_conversion_rate(node: Element) -> schema.ConversionRate:
    return schema.ConversionRate(
        from_ccy=node.attrib["fromCurrency"],
        to_ccy=node.attrib["toCurrency"],
        rate=float(node.attrib["rate"]),
    )


def _parse_conversion_rates(node: Element) -> schema.ConversionRates:
    return schema.ConversionRates(
        entries=[_parse_conversion_rate(rate_node) for rate_node in list(node)],
    )


def _parse_flex_statement_entries(nodes: list[Element]) -> schema.FlexStatementEntries:
    account_information: schema.AccountInformation | None = None
    mtm_performance_summary_in_base: schema.MTMPerformanceSummaryInBase | None = None
    securities_info: schema.SecuritiesInfo | None = None
    conversion_rates: schema.ConversionRates | None = None
    for node in nodes:
        node_type = node.tag
        if node_type == "AccountInformation":
            account_information = _parse_account_information(node)
        elif node_type == "MTMPerformanceSummaryInBase":
            mtm_performance_summary_in_base = _parse_mtm_performance_summary_in_base(node)
        elif node_type == "SecuritiesInfo":
            securities_info = _parse_securities_info(node)
        elif node_type == "ConversionRates":
            conversion_rates = _parse_conversion_rates(node)
    return schema.FlexStatementEntries(
        account_information=account_information,
        mtm_performance_summary_in_base=mtm_performance_summary_in_base,
        securities_info=securities_info,
        conversion_rates=conversion_rates,
    )


def _parse_flex_statement(node: Element) -> schema.FlexStatement:
    return schema.FlexStatement(
        account_id=node.attrib["accountId"],
        from_date=date.fromisoformat(node.attrib["fromDate"]),
        to_date=date.fromisoformat(node.attrib["toDate"]),
        period=node.attrib["period"],
        entries=_parse_flex_statement_entries(list(node)),
    )


def _parse_flex_report(report_root: Element) -> schema.FlexReport:
    try:
        assert report_root is not None
        assert report_root.tag == "FlexQueryResponse"
        flex_statements_node = report_root.find("FlexStatements")
        assert isinstance(flex_statements_node, Element)
        return schema.FlexReport(
            query_name=report_root.attrib["queryName"],
            statements=[
                _parse_flex_statement(flex_statement_node) for flex_statement_node in list(flex_statements_node)
            ],
            messages=[str(message_node.text) for message_node in list(report_root.findall("Message"))],
        )
    except Exception as e:
        raise FlexReportParserError(f"while extracting Flex report content: {e}") from e


def parse_flex_report_payload(xml_payload: str) -> schema.FlexReport:
    try:
        return _parse_flex_report(parse_xml_payload(xml_payload))
    except XMLParseError as e:
        raise FlexReportParserError(f"while parsing XML Flex report: {e}") from e


def parse_flex_report_file(report_file_path: Path) -> schema.FlexReport:
    try:
        tree = parse_xml_file(str(report_file_path.expanduser().absolute()))
        return _parse_flex_report(tree.getroot())
    except XMLParseError as e:
        raise FlexReportParserError(f"while parsing XML Flex report: {e}") from e
