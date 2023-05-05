from typing import Any

from finbot.clients.base import Base as ClientBase


class HistoryClient(ClientBase):
    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def write_history(self, snapshot_id: str) -> Any:
        return self.post(
            f"history/{snapshot_id}/write/",
            payload={},
        )
