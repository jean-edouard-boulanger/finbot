from finbot.apps.appwsrv.agent import schema as agent_schema
from finbot.apps.appwsrv.agent.tools.base import ToolResult, render_tool


@render_tool(
    description=(
        "Display a data table to the user. Up to 12 rows, up to 5 columns. First column is the "
        "row label; subsequent columns right-align as numeric. Use for rankings and structured "
        "comparisons (top categories, top holdings, subscription list). "
        "At most ONE present_* tool per response unless the user explicitly asks for multiple views."
    ),
    icon="table",
    label="Preparing table",
)
def present_table(args: agent_schema.TableBlock) -> ToolResult:
    return ToolResult(payload={"acknowledged": True}, summary=args.title, rich_block=args)
