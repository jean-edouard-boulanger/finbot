import abc
from typing import Any, Self

from finbot.providers.errors import RetiredProviderError
from finbot.providers.schema import Assets, Balances, Liabilities


class ProviderBase(object):
    def __init__(self, **kwargs: Any):
        pass

    @staticmethod
    @abc.abstractmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "ProviderBase":
        raise NotImplementedError("create")

    @staticmethod
    @abc.abstractmethod
    def description() -> str:
        raise NotImplementedError("description")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        pass

    @abc.abstractmethod
    def initialize(self) -> None:
        """Perform any initializations needed before balances/assets/liabilities
        can be retrieved from the associated linked account. This includes
        (but is not limited to) authentication, initialization of resources
        needed by the provider, etc.
        """
        pass

    def get_balances(self) -> Balances:
        """Retrieve all accounts and respective balances associated with this linked account"""
        return Balances(accounts=[])

    def get_assets(self) -> Assets:
        """Retrieve all accounts and respective assets associated with this linked account"""
        return Assets(accounts=[])

    def get_liabilities(self) -> Liabilities:
        """Retrieve all accounts and respective liabilities associated with this linked account"""
        return Liabilities(accounts=[])


class RetiredProvider(ProviderBase):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        raise RetiredProviderError()

    @staticmethod
    @abc.abstractmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "ProviderBase":
        raise RetiredProviderError()

    @staticmethod
    @abc.abstractmethod
    def description() -> str:
        return "Retired provider"
