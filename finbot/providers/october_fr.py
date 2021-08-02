from finbot.providers import retired
from finbot.providers.selenium_based import SeleniumBased


AUTH_URL = "https://app.october.eu/login"
PORTFOLIO_URL = "https://app.october.eu/transactions/summary"
LOANS_URL = "https://app.october.eu/transactions/loans"


class Credentials(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    @property
    def user_id(self):
        return self.username

    @staticmethod
    def init(data):
        return Credentials(data["username"], data["password"])


@retired
class Api(SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
