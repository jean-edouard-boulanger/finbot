from finbot.apps.appwsrv.agent import schema as agent_schema
from finbot.apps.appwsrv.agent.tools.base import ToolResult, render_tool


@render_tool(
    description=(
        "Display a chart (line / area / bar) to visualise a trend or comparison. Up to 36 x-axis "
        "labels and 5 series. For monetary axes set y_unit to a 3-letter currency code (e.g. 'GBP'); "
        "for percentages set '%'. Use line/area for time series, bar for categorical comparisons. "
        "Call AFTER you've gathered the underlying data via a data tool. "
        "At most ONE present_* tool per response unless the user explicitly asks for multiple views."
    ),
    icon="chart",
    label="Plotting chart",
)
def present_chart(args: agent_schema.ChartBlock) -> ToolResult:
    return ToolResult(payload={"acknowledged": True}, summary=args.title, rich_block=args)
