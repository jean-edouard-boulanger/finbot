from typing import Any
from datetime import datetime


class Base(object):
    def __init__(self, **kwargs):
        pass

    def authenticate(self, credentials):
        """Authenticate user with provided credentials. Should persist any
        information needed to perform further operations (get balances,
        get assets, get liabilities)

        :raises AuthFailure: should be raised if authentication failed
        """
        pass

    def get_balances(self) -> dict[Any, Any]:
        """ """
        return {"accounts": []}

    def get_assets(self) -> dict[Any, Any]:
        """ """
        return {"accounts": []}

    def get_liabilities(self) -> dict[Any, Any]:
        """ """
        return {"accounts": []}

    def get_transactions(
        self, from_date: datetime, to_date: datetime
    ) -> dict[Any, Any]:
        """ """
        return {"accounts": []}

    def close(self):
        """Implement to release any used resource at the end of the session"""
        pass


class RetiredProviderError(RuntimeError):
    pass


def retired(cls):
    def init_override(*args, **kwargs):
        raise RetiredProviderError("This provider has been retired")

    cls.__init__ = init_override
    return cls
