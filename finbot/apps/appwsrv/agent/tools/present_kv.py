from finbot.apps.appwsrv.agent import schema as agent_schema
from finbot.apps.appwsrv.agent.tools.base import ToolResult, render_tool


@render_tool(
    description=(
        "Display a labelled key/value summary panel to the user. Use to surface a small set of "
        "headline figures (e.g. a net-worth breakdown). Tones colour the value: 'up' (green), "
        "'down' (red), 'neutral' (default). Call AFTER you've gathered data via the data tools. "
        "At most ONE present_* tool per response unless the user explicitly asks for multiple views."
    ),
    icon="kv",
    label="Preparing summary",
)
def present_kv(args: agent_schema.KvBlock) -> ToolResult:
    return ToolResult(payload={"acknowledged": True}, summary=args.title, rich_block=args)
