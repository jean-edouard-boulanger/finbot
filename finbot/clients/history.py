from finbot.clients.base import Base as ClientBase
from finbot.core import tracer

from typing import Any, Optional


class HistoryClient(ClientBase):
    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def write_history(
        self, snapshot_id: str, tracer_context: Optional[tracer.FlatContext] = None
    ) -> dict[Any, Any]:
        return self.post(
            f"history/{snapshot_id}/write",
            payload=tracer.pack_context({}, tracer_context),
        )
