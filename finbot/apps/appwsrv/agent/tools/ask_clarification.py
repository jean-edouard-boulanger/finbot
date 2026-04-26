from finbot.apps.appwsrv.agent import schema as agent_schema
from finbot.apps.appwsrv.agent.tools.base import ToolResult, render_tool


@render_tool(
    description=(
        "Ask the user to disambiguate before proceeding. Use ONLY when the question is genuinely "
        "ambiguous and you cannot reasonably guess (e.g. an unspecified date range that could mean "
        "two clearly different periods, or a metric that could refer to multiple linked accounts). "
        "Provide 2-4 mutually exclusive options. After calling this, write NO text response — the "
        "clarification block IS the message. Do not call any other tool in the same turn."
    ),
    icon="clarification",
    label="Asking for clarification",
)
def ask_clarification(args: agent_schema.ClarificationBlock) -> ToolResult:
    return ToolResult(payload={"acknowledged": True}, summary=args.title, rich_block=args)
