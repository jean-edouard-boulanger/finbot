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
    "iso_currency": "GBP"
}


class Api(providers.Base):
    def __init__(self, *args, **kwargs):
        pass

    def authenticate(self, *args, **kwargs):
        pass

    def get_balances(self):
        return {
            "accounts": [
                {
                    "account": deepcopy(DUMMY_ACCOUNT),
                    "balance": DUMMY_BALANCE
                }
            ]
        }

    def get_assets(self):
        return {
            "accounts": [
                {
                    "account": deepcopy(DUMMY_ACCOUNT),
                    "assets": [{
                        "name": "cash",
                        "type": "currency",
                        "value": DUMMY_BALANCE
                    }]
                }
            ]
        }
