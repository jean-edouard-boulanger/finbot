from finbot.apps.appwsrv.agent.tools.base import NoArgs, ToolResult, data_tool
from finbot.core.schema import BaseModel
from finbot.model import SessionType, repository


class _Account(BaseModel):
    name: str
    provider_id: str
    value: float
    currency: str
    change_1day_pct: float | None


class _Payload(BaseModel):
    valuation_currency: str
    accounts: list[_Account]


@data_tool(
    description="Get the current valuation per linked account (bank, broker, etc.) sorted by value.",
    icon="trending",
    label="Listing linked accounts",
)
def get_accounts_breakdown(session: SessionType, user_account_id: int, args: NoArgs) -> ToolResult:
    history = repository.get_last_history_entry(session, user_account_id)
    settings = repository.get_user_account_settings(session, user_account_id)
    rows = repository.find_linked_accounts_valuation(session, history.id)
    accounts: list[_Account] = []
    for entry in sorted(rows, key=lambda e: -1.0 * float(e.valuation)):
        if entry.linked_account.deleted:
            continue
        change_1d = entry.valuation_change.change_1day
        value = float(entry.valuation)
        change_pct = (float(change_1d) / value * 100.0) if change_1d is not None and value else None
        accounts.append(
            _Account(
                name=entry.linked_account.account_name,
                provider_id=entry.linked_account.provider_id,
                value=value,
                currency=history.valuation_ccy,
                change_1day_pct=change_pct,
            )
        )
    payload = _Payload(valuation_currency=settings.valuation_ccy, accounts=accounts)
    return ToolResult(payload=payload, summary=f"{len(accounts)} linked accounts")
