from finbot import providers
from copy import deepcopy


class Credentials(object):
    @property
    def user_id(self):
        return "dummy"

    @staticmethod
    def init(_):
        return Credentials()


DUMMY_BALANCE = 1000.0
DUMMY_ACCOUNT = {
    "id": "dummy",
    "name": "Dummy account",
    "iso_currency": "GBP",
    "type": "cash"
}


class Api(providers.Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def authenticate(self, _):
        pass

    def get_balances(self):
        return {
            "accounts": [
                {
                    "account": deepcopy(DUMMY_ACCOUNT),
                    "balance": DUMMY_BALANCE,
                }
            ]
        }

    def get_assets(self):
        return {
            "accounts": [
                {
                    "account": deepcopy(DUMMY_ACCOUNT),
                    "assets": [{
                        "name": "Cash",
                        "type": "currency",
                        "value": DUMMY_BALANCE,
                    }]
                }
            ]
        }
