import base64
from typing import Any

from pydantic import SecretStr

from finbot.core.schema import BaseModel, CurrencyCode
from finbot.core.secure import async_pgp_decrypt
from finbot.core.utils import some
from finbot.providers import schema as providers_schema
from finbot.providers.base import ProviderBase
from finbot.providers.errors import UnsupportedFinancialInstrument
from finbot.providers.interactive_brokers_uk.flex_report.parser import (
    parse_flex_report_payload,
)
from finbot.providers.interactive_brokers_uk.flex_report.schema import (
    AccountInformation,
    FlexReport,
    FlexStatement,
    FlexStatementEntries,
    OpenPosition,
)
from finbot.providers.interactive_brokers_uk.intake import (
    IntakeMethod,
    async_load_latest_report_payload,
)
from finbot.providers.schema import Account, AccountType


class PGPKey(BaseModel):
    data_base64: SecretStr
    passphrase: SecretStr | None = None

    @property
    def pgp_key(self) -> bytes:
        return base64.b64decode(self.data_base64.get_secret_value())


class Credentials(BaseModel):
    report_file_pattern: str = "*.xml"
    intake_method: IntakeMethod
    pgp_key: PGPKey | None


class Api(ProviderBase):
    description = "Interactive Brokers (UK)"
    credentials_type = Credentials

    def __init__(self, credentials: Credentials, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._credentials = credentials
        self.__report: FlexReportWrapper | None = None

    async def initialize(self) -> None:
        raw_report_payload = await async_load_latest_report_payload(
            self._credentials.report_file_pattern,
            self._credentials.intake_method,
        )
        if pgp_key := self._credentials.pgp_key:
            report_payload = (
                await async_pgp_decrypt(
                    pgp_key_blob=pgp_key.pgp_key,
                    passphrase=pgp_key.passphrase.get_secret_value() if pgp_key.passphrase else None,
                    encrypted_blob=raw_report_payload,
                )
            ).decode()
        else:
            report_payload = raw_report_payload.decode()
        self.__report = FlexReportWrapper(parse_flex_report_payload(report_payload))

    async def get_accounts(self) -> list[Account]:
        return [statement.account for statement in some(self.__report).statements]

    async def get_assets(self) -> providers_schema.Assets:
        return providers_schema.Assets(
            accounts=[statement.get_assets(self.user_account_currency) for statement in some(self.__report).statements],
        )


class FlexStatementWrapper:
    def __init__(self, statement: FlexStatement):
        self.statement = statement
        self.account = providers_schema.Account(
            id=self.account_id,
            name=self.account_name,
            iso_currency=self.account_information.currency,
            type=AccountType.investment,
            sub_type="brokerage",
        )

    @property
    def account_id(self) -> str:
        return self.statement.account_id

    @property
    def entries(self) -> FlexStatementEntries:
        return self.statement.entries

    @property
    def account_currency(self) -> CurrencyCode:
        return self.account_information.currency

    @property
    def account_information(self) -> AccountInformation:
        return some(self.entries.account_information)

    @property
    def account_name(self) -> str:
        if self.account_information.alias:
            return f"{self.account_information.alias} ({self.account_id})"
        return self.account_id

    def get_assets(self, user_account_currency: CurrencyCode) -> providers_schema.AssetsEntry:
        cash_assets = [
            providers_schema.Asset.cash(
                currency=entry.currency,
                is_domestic=entry.currency == user_account_currency,
                amount=entry.ending_cash,
            )
            for entry in some(self.entries.cash_report).entries
        ]
        return providers_schema.AssetsEntry(
            account_id=self.account.id,
            items=cash_assets + [_make_asset(entry=entry) for entry in some(self.entries.open_positions).entries],
        )


class FlexReportWrapper:
    def __init__(self, report: FlexReport):
        self.report = report
        self.statements = [FlexStatementWrapper(entry) for entry in report.statements]


def _make_asset(
    entry: OpenPosition,
) -> providers_schema.Asset:
    asset_category = entry.asset_category
    if asset_category == "STK":
        return providers_schema.Asset(
            name=f"{entry.symbol} - {entry.description}",
            type="equity",
            asset_class=providers_schema.AssetClass.equities,
            asset_type=providers_schema.AssetType.stock,
            value_in_item_ccy=entry.position_value,
            units=entry.position,
            currency=entry.currency,
            isin_code=entry.isin if entry.isin else None,
            provider_specific={
                "Symbol": entry.symbol,
                "Description": entry.description,
                "Side": entry.side.value.lower(),
                entry.security_id_type: entry.security_id,
                "Stock currency": entry.currency,
                "Listing exchange": entry.listing_exchange,
                "Report date": entry.report_date.strftime("%Y-%b-%d"),
            },
        )
    raise UnsupportedFinancialInstrument(asset_category, entry.symbol)
