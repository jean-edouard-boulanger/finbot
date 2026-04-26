"""Agent tools package — one module per tool, assembled into a registry here.

Each tool module exposes a single `ToolSpec` named after the tool. The decorator-based
declaration (`@data_tool` / `@render_tool`) is in `base.py`.
"""

from typing import Any

from finbot.apps.appwsrv.agent.tools.accounts_breakdown import get_accounts_breakdown
from finbot.apps.appwsrv.agent.tools.ask_clarification import ask_clarification
from finbot.apps.appwsrv.agent.tools.base import NoArgs, ToolResult, ToolSpec, data_tool, render_tool
from finbot.apps.appwsrv.agent.tools.holdings import get_holdings
from finbot.apps.appwsrv.agent.tools.net_worth import get_net_worth
from finbot.apps.appwsrv.agent.tools.present_callout import present_callout
from finbot.apps.appwsrv.agent.tools.present_chart import present_chart
from finbot.apps.appwsrv.agent.tools.present_kv import present_kv
from finbot.apps.appwsrv.agent.tools.present_table import present_table
from finbot.apps.appwsrv.agent.tools.savings_rate import get_savings_rate
from finbot.apps.appwsrv.agent.tools.search_transactions import search_transactions
from finbot.apps.appwsrv.agent.tools.spending_breakdown import get_spending_breakdown
from finbot.apps.appwsrv.agent.tools.subscriptions import get_subscriptions
from finbot.apps.appwsrv.agent.tools.valuation_history import get_valuation_history

ALL_TOOLS: list[ToolSpec[Any]] = [
    get_net_worth,
    get_accounts_breakdown,
    get_valuation_history,
    get_spending_breakdown,
    search_transactions,
    get_subscriptions,
    get_holdings,
    get_savings_rate,
    present_kv,
    present_table,
    present_chart,
    present_callout,
    ask_clarification,
]

TOOLS_BY_NAME: dict[str, ToolSpec[Any]] = {t.name: t for t in ALL_TOOLS}
OPENAI_TOOLS: list[dict[str, Any]] = [t.to_openai_tool() for t in ALL_TOOLS]

__all__ = [
    "ALL_TOOLS",
    "NoArgs",
    "OPENAI_TOOLS",
    "TOOLS_BY_NAME",
    "ToolResult",
    "ToolSpec",
    "data_tool",
    "render_tool",
]
