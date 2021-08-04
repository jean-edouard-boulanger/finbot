from finbot.providers.selenium_based import SeleniumBased
from finbot.providers import retired

from typing import Any


class Credentials(object):
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    @property
    def user_id(self) -> str:
        return self.username

    @staticmethod
    def init(data: dict[str, Any]) -> "Credentials":
        return Credentials(data["username"], data["password"])


@retired
class Api(SeleniumBased):
    def __init__(self) -> None:
        super().__init__()
