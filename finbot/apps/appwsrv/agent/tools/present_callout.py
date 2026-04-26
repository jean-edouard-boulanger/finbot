from finbot.apps.appwsrv.agent import schema as agent_schema
from finbot.apps.appwsrv.agent.tools.base import ToolResult, render_tool


@render_tool(
    description=(
        "Display a single coloured callout for ONE genuinely important insight or recommendation "
        "(e.g. 'You're on track to hit your savings goal'). Tones: 'success' (green) or "
        "'warning' (amber) only. "
        "DO NOT use this as a section header, summary box, or follow-up suggestion — answer in plain "
        "text. Use at most once per response, and only when there is a real call-to-action or insight."
    ),
    icon="callout",
    label="Highlighting insight",
)
def present_callout(args: agent_schema.CalloutBlock) -> ToolResult:
    return ToolResult(payload={"acknowledged": True}, summary=args.title, rich_block=args)
