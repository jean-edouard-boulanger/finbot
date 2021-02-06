from typing import Optional, List, Dict
from dataclasses import dataclass

from finbot.model import UserAccount


@dataclass
class Request:
    user_account_id: int
    linked_accounts: Optional[List[int]] = None

    def serialize(self):
        return {
            "user_account_id": self.user_account_id,
            "linked_accounts": self.linked_accounts
        }

    @staticmethod
    def deserialize(data: Dict):
        return Request(
            user_account_id=data["user_account_id"],
            linked_accounts=data.get("linked_accounts")
        )