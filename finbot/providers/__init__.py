class Base(object):
    def authenticate(self, credentials):
        raise NotImplementedError("authenticate must be implemented")

    def get_balances(self, account_ids=None):
        return {"accounts": []}

    def get_assets(self, account_ids=None):
        return {"accounts": []}

    def get_liabilities(self, account_ids=None):
        return {"accounts": []}

    def close(self):
        pass
