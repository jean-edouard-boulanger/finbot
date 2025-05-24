from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ParseError as XMLParseError
from xml.etree.ElementTree import fromstring as parse_xml_payload
from xml.etree.ElementTree import parse as parse_xml_file

from finbot.core.pydantic_ import ValidationError as PydanticValidationError
from finbot.core.schema import BaseModelT
from finbot.providers.interactive_brokers_uk.flex_report import schema


class FlexReportParserError(Exception):
    pass


def _snake_case_to_camel_case(field_name: str) -> str:
    items = field_name.split("_")
    formatted_items = [items[0]] + [item.capitalize() for item in items[1:]]
    return "".join(formatted_items)


@dataclass(frozen=True)
class _FieldMapping:
    xml_field: str
    formatters: list[Callable[[Any], Any]] = field(default_factory=list)


def _parse_xml_to_pydantic(
    model_type: type[BaseModelT],
    node: Element,
    model_to_xml_fields_overrides: dict[str, str | _FieldMapping] | None = None,
) -> BaseModelT:
    raw_payload = {}
    model_to_xml_fields_overrides = model_to_xml_fields_overrides or {}
    for model_field_name in model_type.__fields__:
        if mapping := model_to_xml_fields_overrides.get(model_field_name):
            if isinstance(mapping, _FieldMapping):
                xml_field_name = mapping.xml_field
                xml_value = node.attrib[xml_field_name]
                for formatter in mapping.formatters:
                    xml_value = formatter(xml_value)
            else:
                xml_value = node.attrib[mapping]
        else:
            xml_field_name = _snake_case_to_camel_case(model_field_name)
            xml_value = node.attrib[xml_field_name]
        raw_payload[model_field_name] = xml_value
    try:
        return model_type(**raw_payload)
    except PydanticValidationError as e:
        raise FlexReportParserError(
            f"failed to convert XML to pydantic '{model_type.__name__}' object (extracted payload: {raw_payload})"
        ) from e


def _parse_trade(node: Element) -> schema.Trade:
    return _parse_xml_to_pydantic(model_type=schema.Trade, node=node)


def _parse_trades(node: Element) -> schema.Trades:
    return schema.Trades(
        entries=[
            _parse_trade(child_node)
            for child_node in list(node)
            if node.tag == "Trade" and node.attrib["levelOfDetail"] == "EXECUTION"
        ]
    )


def _parse_mtm_performance_summary_underlying(
    node: Element,
) -> schema.MTMPerformanceSummaryUnderlying:
    return _parse_xml_to_pydantic(
        model_type=schema.MTMPerformanceSummaryUnderlying,
        node=node,
        model_to_xml_fields_overrides={
            "security_id": "securityID",
            "security_id_type": "securityIDType",
        },
    )


def _parse_mtm_performance_summary_in_base(
    node: Element,
) -> schema.MTMPerformanceSummaryInBase:
    return schema.MTMPerformanceSummaryInBase(
        entries=[
            _parse_mtm_performance_summary_underlying(child_node)
            for child_node in list(node)
            if child_node.attrib["symbol"] != ""
        ]
    )


def _parse_open_position(
    node: Element,
) -> schema.OpenPosition:
    return _parse_xml_to_pydantic(
        model_type=schema.OpenPosition,
        node=node,
        model_to_xml_fields_overrides={
            "security_id": "securityID",
            "security_id_type": "securityIDType",
            "side": _FieldMapping(xml_field="side", formatters=[str.lower]),
        },
    )


def _parse_open_positions(
    node: Element,
) -> schema.OpenPositions:
    return schema.OpenPositions(entries=[_parse_open_position(child_node) for child_node in list(node)])


def _parse_cash_report_currency(
    node: Element,
) -> schema.CashReportCurrency:
    return _parse_xml_to_pydantic(
        model_type=schema.CashReportCurrency,
        node=node,
    )


def _parse_cash_report(
    node: Element,
) -> schema.CashReport:
    return schema.CashReport(
        entries=[
            _parse_cash_report_currency(child_node)
            for child_node in list(node)
            if child_node.attrib["levelOfDetail"] == "Currency"
        ]
    )


def _parse_account_information(node: Element) -> schema.AccountInformation:
    return _parse_xml_to_pydantic(
        model_type=schema.AccountInformation,
        node=node,
        model_to_xml_fields_overrides={
            "alias": "acctAlias",
        },
    )


def _parse_security_info(node: Element) -> schema.SecurityInfo:
    return _parse_xml_to_pydantic(
        model_type=schema.SecurityInfo,
        node=node,
        model_to_xml_fields_overrides={
            "security_id": "securityID",
            "security_id_type": "securityIDType",
        },
    )


def _parse_securities_info(node: Element) -> schema.SecuritiesInfo:
    return schema.SecuritiesInfo(
        entries=[_parse_security_info(security_node) for security_node in list(node)],
    )


def _parse_conversion_rate(node: Element) -> schema.ConversionRate:
    return _parse_xml_to_pydantic(
        model_type=schema.ConversionRate,
        node=node,
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
    open_positions: schema.OpenPositions | None = None
    cash_report: schema.CashReport | None = None
    trades: schema.Trades | None = None
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
        elif node_type == "OpenPositions":
            open_positions = _parse_open_positions(node)
        elif node_type == "CashReport":
            cash_report = _parse_cash_report(node)
        elif node_type == "Trades":
            trades = _parse_trades(node)
    return schema.FlexStatementEntries(
        account_information=account_information,
        mtm_performance_summary_in_base=mtm_performance_summary_in_base,
        securities_info=securities_info,
        conversion_rates=conversion_rates,
        open_positions=open_positions,
        cash_report=cash_report,
        trades=trades,
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
