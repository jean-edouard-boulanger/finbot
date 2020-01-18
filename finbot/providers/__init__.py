class Base(object):
    def authenticate(self, credentials):
        """ Authenticate user with provided credentials. Should persist any
        informations needed to perform further operations (get balances, 
        get assets, get liabilities)

        :raises AuthFailure: should be raised if authentication failed
        """
        pass

    def get_balances(self, account_ids=None):
        """
        """
        return {"accounts": []}

    def get_assets(self, account_ids=None):
        """
        """
        return {"accounts": []}

    def get_liabilities(self, account_ids=None):
        """
        """
        return {"accounts": []}

    def close(self):
        """ Implement to release any used resource at the end of the session
        """
        pass
