from typing import Any, Generator, cast

from pydantic import BaseModel, SecretStr

from finbot.core.environment import get_saxo_gateway_url
from finbot.core.saxo import SaxoGatewayClient, SaxoGatewaySettings
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationFailure
from finbot.providers.schema import (
    Account,
    Asset,
    Assets,
    AssetsEntry,
    BalanceEntry,
    Balances,
)


class Credentials(BaseModel):
    api_key: SecretStr


class Api(ProviderBase):
    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        saxo_gateway_url = get_saxo_gateway_url()
        assert saxo_gateway_url is not None
        self._client = SaxoGatewayClient(
            settings=SaxoGatewaySettings(gateway_url=saxo_gateway_url),
            api_key=credentials.api_key.get_secret_value(),
        )
        self._accounts: list[Any] | None = None

    @staticmethod
    def description() -> str:
        return "Saxo OpenAPI Gateway (FR)"

    @staticmethod
    def create(authentication_payload: dict[str, Any], **kwargs: Any) -> "Api":
        return Api(Credentials.parse_obj(authentication_payload), **kwargs)

    def initialize(self) -> None:
        try:
            self._accounts = self._client.openapi_get("port/v1/accounts/me")["Data"]
        except Exception as e:
            raise AuthenticationFailure(str(e))

    def iter_accounts(self) -> Generator[tuple[Account, Any], None, None]:
        assert self._accounts is not None
        for raw_account_data in self._accounts:
            yield Account(
                id=raw_account_data["AccountKey"],
                name=raw_account_data["AccountGroupName"],
                iso_currency=raw_account_data["Currency"],
                type="investment",
            ), raw_account_data

    def get_balances(self) -> Balances:
        return Balances(
            accounts=[
                BalanceEntry(
                    account=account,
                    balance=self._get_account_balance(
                        account_key=raw_account_data["AccountKey"],
                        client_key=raw_account_data["ClientKey"],
                    ),
                )
                for (account, raw_account_data) in self.iter_accounts()
            ]
        )

    def get_assets(self) -> Assets:
        return Assets(
            accounts=[
                AssetsEntry(
                    account=account,
                    assets=self._get_account_assets(
                        account_key=raw_account_data["AccountKey"],
                        client_key=raw_account_data["ClientKey"],
                    ),
                )
                for (account, raw_account_data) in self.iter_accounts()
            ]
        )

    def _get_account_assets(self, account_key: str, client_key: str) -> list[Asset]:
        assets: list[Asset] = []
        balance_data = self._client.openapi_get(
            f"port/v1/balances?AccountKey={account_key}&ClientKey={client_key}"
        )
        if cash_available := balance_data.get("CashAvailableForTrading"):
            assets.append(Asset(name="Cash", type="currency", value=cash_available))
        return assets

    def _get_account_balance(self, account_key: str, client_key: str) -> float:
        balance_data = self._client.openapi_get(
            f"port/v1/balances?AccountKey={account_key}&ClientKey={client_key}"
        )
        return cast(float, balance_data["TotalValue"])
