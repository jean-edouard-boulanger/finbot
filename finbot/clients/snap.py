from finbot.clients.base import Base as ClientBase
from finbot.core import tracer

from typing import Any, Optional


class SnapClient(ClientBase):
    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def take_snapshot(
        self,
        account_id: int,
        linked_accounts: Optional[list[int]] = None,
        tracer_context: Optional[tracer.FlatContext] = None,
    ) -> dict[Any, Any]:
        return self.post(
            f"snapshot/{account_id}/take",
            tracer.pack_context({"linked_accounts": linked_accounts}, tracer_context),
        )
