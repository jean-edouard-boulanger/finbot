from finbot import providers


class Credentials(object):
    def __init__(self, api_key: str, private_key: str):
        self.api_key = api_key
        self.private_key = private_key

    @property
    def user_id(self) -> str:
        return "<private>"

    @staticmethod
    def init(data: dict[str, str]) -> "Credentials":
        return Credentials(data["api_key"], data["private_key"])


@providers.retired
class Api(providers.Base):
    pass
