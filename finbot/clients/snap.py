from finbot.clients.base import Base as ClientBase

from typing import Any, Optional


class SnapClient(ClientBase):
    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def take_snapshot(
        self,
        account_id: int,
        linked_accounts: Optional[list[int]] = None,
    ) -> Any:
        return self.post(
            f"snapshot/{account_id}/take", {"linked_accounts": linked_accounts}
        )
