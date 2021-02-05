from typing import Optional, List
from dataclasses import dataclass

from finbot.model import UserAccount


@dataclass
class Request:
    user_account: UserAccount
    linked_accounts: Optional[List[int]] = None
