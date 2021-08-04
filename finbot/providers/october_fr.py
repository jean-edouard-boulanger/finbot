from finbot.providers import retired
from finbot.providers.selenium_based import SeleniumBased

from typing import Any

AUTH_URL = "https://app.october.eu/login"
PORTFOLIO_URL = "https://app.october.eu/transactions/summary"
LOANS_URL = "https://app.october.eu/transactions/loans"


class Credentials(object):
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    @property
    def user_id(self) -> str:
        return self.username

    @staticmethod
    def init(data: dict[Any, Any]) -> "Credentials":
        return Credentials(data["username"], data["password"])


@retired
class Api(SeleniumBased):
    def __init__(self) -> None:
        super().__init__()
