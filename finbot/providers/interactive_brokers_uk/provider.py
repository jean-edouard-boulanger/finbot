import base64
import logging
from contextlib import contextmanager
from functools import cached_property
from typing import Any, Generator, cast

import pgpy
from pydantic import BaseModel, SecretStr

from finbot.core.utils import some
from finbot.providers.base import ProviderBase
from finbot.providers.interactive_brokers_uk.flex_report_parser import (
    FlexStatement,
    MTMPerformanceSummaryUnderlying,
    SecurityInfo,
    parse_flex_report_payload,
)
from finbot.providers.interactive_brokers_uk.intake import (
    IntakeMethod,
    load_latest_report_payload,
)
from finbot.providers.schema import (
    Account,
    Asset,
    AssetClass,
    Assets,
    AssetsEntry,
    AssetType,
    BalanceEntry,
    Balances,
    CurrencyCode,
)


class PGPKey(BaseModel):
    data_base64: SecretStr
    passphrase: SecretStr | None = None

    @contextmanager
    def unlocked_pgp_key(self) -> Generator[pgpy.PGPKey, None, None]:
        pgp_key_data = base64.b64decode(self.data_base64.get_secret_value())
        pgp_key: pgpy.PGPKey = pgpy.PGPKey.from_blob(pgp_key_data)[0]
        if self.passphrase:
            with pgp_key.unlock(self.passphrase.get_secret_value()):
                yield pgp_key
                return
        yield pgp_key


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
        self.__statement: FlexStatement | None = None

    def initialize(self) -> None:
        raw_report_payload = load_latest_report_payload(
            self._credentials.report_file_pattern, self._credentials.intake_method
        )
        if self._credentials.pgp_key:
            with self._credentials.pgp_key.unlocked_pgp_key() as pgp_key:
                report_payload = _attempt_decrypt_flex_report_payload(
                    raw_report_payload, pgp_key
                )
        else:
            report_payload = raw_report_payload.decode()
        report = parse_flex_report_payload(report_payload)
        assert len(report.statements) == 1
        self.__statement = report.statements[0]

    @property
    def _statement(self) -> FlexStatement:
        return some(self.__statement)

    @cached_property
    def _account(self) -> Account:
        account_info = some(self._statement.entries.account_information)
        return Account(
            id=account_info.account_id,
            name=account_info.alias or account_info.account_id,
            iso_currency=CurrencyCode(account_info.currency),
            type="investment",
        )

    @cached_property
    def _conversion_rates(self) -> dict[tuple[CurrencyCode, CurrencyCode], float]:
        entries = some(self._statement.entries.conversion_rates).entries
        return {
            (CurrencyCode(entry.from_ccy), CurrencyCode(entry.to_ccy)): entry.rate
            for entry in entries
        }

    @cached_property
    def _securities(self) -> dict[str, SecurityInfo]:
        entries = some(self._statement.entries.securities_info).entries
        return {entry.full_security_id: entry for entry in entries}

    def get_balances(self) -> Balances:
        assert self._statement.entries.mtm_performance_summary_in_base is not None
        conversion_rates = self._conversion_rates
        securities = self._securities
        portfolio_entries = (
            self._statement.entries.mtm_performance_summary_in_base.entries
        )
        return Balances(
            accounts=[
                BalanceEntry(
                    account=self._account,
                    balance=sum(
                        _make_asset(
                            entry=entry,
                            conversion_rates=conversion_rates,
                            securities=securities,
                            account_currency=self._account.iso_currency,
                            user_account_currency=self.user_account_currency,
                        ).value
                        for entry in portfolio_entries
                    ),
                )
            ]
        )

    def get_assets(self) -> Assets:
        assert self._statement.entries.mtm_performance_summary_in_base is not None
        conversion_rates = self._conversion_rates
        securities = self._securities
        portfolio_entries = (
            self._statement.entries.mtm_performance_summary_in_base.entries
        )
        return Assets(
            accounts=[
                AssetsEntry(
                    account=self._account,
                    assets=[
                        _make_asset(
                            entry=entry,
                            conversion_rates=conversion_rates,
                            securities=securities,
                            account_currency=self._account.iso_currency,
                            user_account_currency=self.user_account_currency,
                        )
                        for entry in portfolio_entries
                    ],
                )
            ]
        )


def _make_asset(
    entry: MTMPerformanceSummaryUnderlying,
    conversion_rates: dict[tuple[CurrencyCode, CurrencyCode], float],
    securities: dict[str, SecurityInfo],
    account_currency: CurrencyCode,
    user_account_currency: CurrencyCode,
) -> Asset:
    asset_category = entry.asset_category
    if asset_category == "STK":
        stock_currency = CurrencyCode(securities[entry.full_security_id].currency)
        conversion_rate = (
            1.0
            if stock_currency == account_currency
            else conversion_rates[(stock_currency, account_currency)]
        )
        return Asset(
            name=f"{entry.symbol} - {entry.description}",
            type="equity",
            asset_class=AssetClass.equities,
            asset_type=AssetType.stock,
            value=entry.close_quantity * entry.close_price * conversion_rate,
            units=entry.close_quantity,
            provider_specific={
                "Symbol": entry.symbol,
                "Description": entry.description,
                entry.security_id_type: entry.security_id,
                "Stock currency": stock_currency,
                "Listing exchange": entry.listing_exchange,
                f"Close price ({stock_currency})": entry.close_price,
                "Report date": entry.report_date.strftime("%Y-%b-%d"),
            },
        )
    elif asset_category == "CASH":
        currency = CurrencyCode(entry.symbol)
        return Asset.cash(
            currency=currency,
            is_domestic=currency == user_account_currency,
            amount=entry.close_quantity * entry.close_price,
            provider_specific={"Report date": entry.report_date.strftime("%Y-%b-%d")},
        )
    raise ValueError(f"unknown asset category: {asset_category}")


def _attempt_decrypt_flex_report_payload(payload: bytes, pgp_key: pgpy.PGPKey) -> str:
    try:
        pgp_message = pgpy.PGPMessage.from_blob(payload)
    except ValueError:
        # This is an indication that we tried to load a clear-text (i.e. not encrypted)
        # flex report payload. In that case, simply attempt to decode.
        logging.debug("report does not appear encrypted, although pgp key was provided")
        return payload.decode()
    return cast(str, pgp_key.decrypt(pgp_message).message)
