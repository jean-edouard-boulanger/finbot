from finbot import providers
from typing import Any

AUTH_URL = "https://app.october.eu/login"


class Credentials(object):
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    @property
    def user_id(self) -> str:
        return self.username

    @staticmethod
    def init(data: dict[str, Any]) -> "Credentials":
        return Credentials(data["username"], data["password"])


@providers.retired
class Api(providers.Base):
    pass
