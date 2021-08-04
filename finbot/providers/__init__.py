from typing import Any, Type, TypeVar, TypedDict, Optional


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
    def authenticate(self, credentials: Any) -> None:
        """Authenticate user with provided credentials. Should persist any
        information needed to perform further operations (get balances,
        get assets, get liabilities)

        :raises AuthFailure: should be raised if authentication failed
        """
        pass

    def get_balances(self) -> Balances:
        """ """
        return {"accounts": []}

    def get_assets(self) -> Assets:
        """ """
        return {"accounts": []}

    def get_liabilities(self) -> Liabilities:
        """ """
        return {"accounts": []}

    def close(self) -> None:
        """Implement to release any used resource at the end of the session"""
        pass


class RetiredProviderError(RuntimeError):
    pass


T = TypeVar("T")


def retired(cls: Type[T]) -> Type[T]:
    def init_override(*args: Any, **kwargs: Any) -> None:
        raise RetiredProviderError("This provider has been retired")

    cls.__init__ = init_override  # type: ignore
    return cls
