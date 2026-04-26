from finbot.apps.appwsrv.agent.tools.base import NoArgs, ToolResult, data_tool
from finbot.apps.appwsrv.reports.holdings import report as holdings_report
from finbot.core.schema import BaseModel
from finbot.model import SessionType, repository


class _Holding(BaseModel):
    name: str
    asset_type: str | None
    asset_class: str | None
    currency: str
    value: float
    account_name: str


class _Payload(BaseModel):
    valuation_currency: str
    total_value: float
    position_count: int
    top_positions: list[_Holding]


@data_tool(
    description=(
        "Get the user's investment portfolio — total value plus the top 50 positions ranked by absolute value."
    ),
    icon="trending",
    label="Fetching portfolio holdings",
)
def get_holdings(session: SessionType, user_account_id: int, args: NoArgs) -> ToolResult:
    history = repository.get_last_history_entry(session, user_account_id)
    settings = repository.get_user_account_settings(session, user_account_id)
    tree = holdings_report.generate(session, history)

    leaves: list[_Holding] = []
    total = 0.0
    for la_node in tree.valuation_tree.children:
        for sa_node in la_node.children:
            for item in sa_node.children:
                value = float(item.valuation.value)
                total += value
                leaves.append(
                    _Holding(
                        name=item.item.name,
                        asset_type=item.item.asset_type,
                        asset_class=item.item.asset_class,
                        currency=item.valuation.currency,
                        value=value,
                        account_name=la_node.linked_account.description,
                    )
                )
    leaves.sort(key=lambda h: -abs(h.value))
    payload = _Payload(
        valuation_currency=settings.valuation_ccy,
        total_value=total,
        position_count=len(leaves),
        top_positions=leaves[:50],
    )
    return ToolResult(payload=payload, summary=f"{len(leaves)} positions")
