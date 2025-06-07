import abc
from typing import Any, Self

from finbot.core import schema as core_schema
from finbot.providers.errors import RetiredProviderError
from finbot.providers.schema import Account, Assets, Liabilities


class ProviderBase:
    description: str
    credentials_type: type[core_schema.BaseModel]

    def __init__(
        self,
        user_account_currency: core_schema.CurrencyCode,
        **kwargs: Any,
    ):
        self.user_account_currency = user_account_currency

    @classmethod
    def create(
        cls,
        authentication_payload: core_schema.CredentialsPayloadType,
        user_account_currency: core_schema.CurrencyCode,
        **kwargs: Any,
    ) -> "ProviderBase":
        return cls(
            credentials=cls.credentials_type.parse_obj(authentication_payload),
            user_account_currency=user_account_currency,
            **kwargs,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        pass

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Perform any initializations needed before balances/assets/liabilities
        can be retrieved from the associated linked account. This includes
        (but is not limited to) authentication, initialization of resources
        needed by the provider, etc.
        """
        pass

    @abc.abstractmethod
    async def get_accounts(self) -> list[Account]:
        """Retrieve all accounts associated with this linked account"""
        pass

    async def get_assets(self) -> Assets:
        """Retrieve all accounts and respective assets associated with this linked account"""
        return Assets(accounts=[])

    async def get_liabilities(self) -> Liabilities:
        """Retrieve all accounts and respective liabilities associated with this linked account"""
        return Liabilities(accounts=[])


class RetiredProvider(ProviderBase):
    credentials_type = core_schema.BaseModel
    description = "Retired provider"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        raise RetiredProviderError()

    async def initialize(self) -> None:
        pass

    async def get_accounts(self) -> list[Account]:
        return []

    @staticmethod
    def create(
        authentication_payload: core_schema.CredentialsPayloadType,
        user_account_currency: core_schema.CurrencyCode,
        **kwargs: Any,
    ) -> "ProviderBase":
        raise RetiredProviderError()
