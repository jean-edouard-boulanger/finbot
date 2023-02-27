import abc
from typing import Any, TypedDict, Optional

from finbot.providers.errors import RetiredProviderError


class Account(TypedDict):
    id: str
    name: str
    iso_currency: str
    type: str


class BalanceEntry(TypedDict):
    account: Account
    balance: float


class Balances(TypedDict):
    accounts: list[BalanceEntry]


class Asset(TypedDict, total=False):
    name: str
    type: str
    value: float
    units: Optional[float]
    provider_specific: Optional[dict[str, Any]]


class AssetEntry(TypedDict):
    account: Account
    assets: list[Asset]


class Assets(TypedDict):
    accounts: list[AssetEntry]


class LiabilityDescription(TypedDict):
    name: str
    type: str
    value: float


class LiabilityEntry(TypedDict):
    account: Account
    liabilities: list[LiabilityDescription]


class Liabilities(TypedDict):
    accounts: list[LiabilityEntry]


class Base(object):
    def __init__(self, **kwargs: Any):
        pass

    @staticmethod
    @abc.abstractmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Base":
        raise NotImplementedError("create")

    @staticmethod
    @abc.abstractmethod
    def description() -> str:
        raise NotImplementedError("description")

    def __enter__(self) -> "Base":
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
        return {"accounts": []}

    def get_assets(self) -> Assets:
        """Retrieve all accounts and respective assets associated with this linked account"""
        return {"accounts": []}

    def get_liabilities(self) -> Liabilities:
        """Retrieve all accounts and respective liabilities associated with this linked account"""
        return {"accounts": []}


class Retired(Base):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        raise RetiredProviderError()

    @staticmethod
    @abc.abstractmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Base":
        raise RetiredProviderError()

    @staticmethod
    @abc.abstractmethod
    def description() -> str:
        return "Retired provider"
