from unittest.mock import Mock, call

import pytest

from finbot.apps.finbotwsrv import schema as finbotwsrv_schema
from finbot.core import fx_market
from finbot.core import schema as core_schema
from finbot.providers import schema as providers_schema
from finbot.services.user_account_snapshot import service
from finbot.services.user_account_snapshot.errors import InconsistentSnapshotData

TEST_USER_ACCOUNT_CCY = core_schema.CurrencyCode.validate("EUR")
ALL_LINE_ITEMS = [
    finbotwsrv_schema.LineItem.Accounts,
    finbotwsrv_schema.LineItem.Assets,
    finbotwsrv_schema.LineItem.Liabilities,
]


@pytest.fixture(scope="function")
def valid_snapshot_data() -> list[service.LinkedAccountSnapshotResult]:
    return [
        service.LinkedAccountSnapshotResult(
            request=service.LinkedAccountSnapshotRequest(
                linked_account_id=1,
                provider_id="dummy_uk",
                credentials_data={},
                line_items=ALL_LINE_ITEMS,
                user_account_currency=TEST_USER_ACCOUNT_CCY,
            ),
            snapshot_data=finbotwsrv_schema.GetFinancialDataResponse(
                financial_data=[
                    finbotwsrv_schema.AccountsResults(
                        results=[
                            providers_schema.Account(
                                id="acc-1",
                                name="Test account 1",
                                iso_currency=TEST_USER_ACCOUNT_CCY,
                                type="depository",
                            ),
                            providers_schema.Account(
                                id="acc-2",
                                name="Test account 2 (credit)",
                                iso_currency=TEST_USER_ACCOUNT_CCY,
                                type="credit",
                            ),
                        ]
                    ),
                    finbotwsrv_schema.AssetsResults(
                        results=[
                            providers_schema.AssetsEntry(
                                account_id="acc-1",
                                items=[
                                    providers_schema.Asset.cash(
                                        currency=TEST_USER_ACCOUNT_CCY,
                                        is_domestic=True,
                                        amount=1000.0,
                                    ),
                                ],
                            ),
                        ]
                    ),
                    finbotwsrv_schema.LiabilitiesResults(
                        results=[
                            providers_schema.LiabilitiesEntry(
                                account_id="acc-2",
                                items=[
                                    providers_schema.Liability(
                                        name="Credit card",
                                        type="credit",
                                        value_in_account_ccy=1000.0,
                                    )
                                ],
                            )
                        ]
                    ),
                ]
            ),
        ),
        service.LinkedAccountSnapshotResult(
            request=service.LinkedAccountSnapshotRequest(
                linked_account_id=2,
                provider_id="dummy_uk",
                credentials_data={},
                line_items=ALL_LINE_ITEMS,
                user_account_currency=TEST_USER_ACCOUNT_CCY,
            ),
            snapshot_data=finbotwsrv_schema.GetFinancialDataResponse(
                financial_data=[
                    finbotwsrv_schema.AccountsResults(
                        results=[
                            providers_schema.Account(
                                id="acc-3",
                                name="Test account 3",
                                iso_currency=core_schema.CurrencyCode.validate("USD"),
                                type="brokerage",
                            )
                        ]
                    ),
                    finbotwsrv_schema.AssetsResults(
                        results=[
                            providers_schema.AssetsEntry(
                                account_id="acc-3",
                                items=[
                                    providers_schema.Asset.cash(
                                        currency=core_schema.CurrencyCode.validate("USD"),
                                        is_domestic=False,
                                        amount=1000.0,
                                    ),
                                    providers_schema.Asset.cash(
                                        currency=core_schema.CurrencyCode.validate("GBP"),
                                        is_domestic=False,
                                        amount=200.0,
                                    ),
                                    providers_schema.Asset(
                                        name="AAPL",
                                        type="stock",
                                        asset_class=providers_schema.AssetClass.equities,
                                        asset_type=providers_schema.AssetType.stock,
                                        value_in_item_ccy=181.18,
                                        units=1.0,
                                        currency=core_schema.CurrencyCode.validate("USD"),
                                    ),
                                    providers_schema.Asset(
                                        name="LVMH",
                                        type="stock",
                                        asset_class=providers_schema.AssetClass.equities,
                                        asset_type=providers_schema.AssetType.stock,
                                        value_in_item_ccy=688.90,
                                        units=1.0,
                                        currency=core_schema.CurrencyCode.validate("EUR"),
                                    ),
                                ],
                            )
                        ]
                    ),
                ]
            ),
        ),
    ]


def test_visit_snapshot_tree(valid_snapshot_data: list[service.LinkedAccountSnapshotResult]):
    visitor_mock = Mock()
    service.visit_snapshot_tree(valid_snapshot_data, visitor_mock)
    assert visitor_mock.visit_linked_account.call_count == 2
    visitor_mock.visit_linked_account.assert_has_calls(
        [
            call(linked_account_id=1, errors=[]),
            call(linked_account_id=2, errors=[]),
        ]
    )
    assert visitor_mock.visit_sub_account.call_count == 3
    visitor_mock.visit_sub_account.assert_has_calls(
        [
            call(
                linked_account_id=1,
                sub_account=providers_schema.Account(
                    id="acc-1",
                    name="Test account 1",
                    iso_currency=TEST_USER_ACCOUNT_CCY,
                    type="depository",
                ),
            ),
            call(
                linked_account_id=1,
                sub_account=providers_schema.Account(
                    id="acc-2",
                    name="Test account 2 (credit)",
                    iso_currency=TEST_USER_ACCOUNT_CCY,
                    type="credit",
                ),
            ),
            call(
                linked_account_id=2,
                sub_account=providers_schema.Account(
                    id="acc-3",
                    name="Test account 3",
                    iso_currency=core_schema.CurrencyCode.validate("USD"),
                    type="brokerage",
                ),
            ),
        ]
    )
    assert visitor_mock.visit_sub_account_item.call_count == 6
    visitor_mock.visit_sub_account_item.assert_has_calls(
        [
            call(
                linked_account_id=1,
                sub_account=providers_schema.Account(
                    id="acc-1",
                    name="Test account 1",
                    iso_currency=TEST_USER_ACCOUNT_CCY,
                    type="depository",
                ),
                item=providers_schema.Asset.cash(
                    currency=TEST_USER_ACCOUNT_CCY,
                    is_domestic=True,
                    amount=1000.0,
                ),
            ),
            call(
                linked_account_id=1,
                sub_account=providers_schema.Account(
                    id="acc-2",
                    name="Test account 2 (credit)",
                    iso_currency=TEST_USER_ACCOUNT_CCY,
                    type="credit",
                ),
                item=providers_schema.Liability(
                    name="Credit card",
                    type="credit",
                    value_in_account_ccy=1000.0,
                ),
            ),
            call(
                linked_account_id=2,
                sub_account=providers_schema.Account(
                    id="acc-3",
                    name="Test account 3",
                    iso_currency=core_schema.CurrencyCode.validate("USD"),
                    type="brokerage",
                ),
                item=providers_schema.Asset.cash(
                    currency=core_schema.CurrencyCode.validate("USD"),
                    is_domestic=False,
                    amount=1000.0,
                ),
            ),
            call(
                linked_account_id=2,
                sub_account=providers_schema.Account(
                    id="acc-3",
                    name="Test account 3",
                    iso_currency=core_schema.CurrencyCode.validate("USD"),
                    type="brokerage",
                ),
                item=providers_schema.Asset.cash(
                    currency=core_schema.CurrencyCode.validate("GBP"),
                    is_domestic=False,
                    amount=200.0,
                ),
            ),
            call(
                linked_account_id=2,
                sub_account=providers_schema.Account(
                    id="acc-3",
                    name="Test account 3",
                    iso_currency=core_schema.CurrencyCode.validate("USD"),
                    type="brokerage",
                ),
                item=providers_schema.Asset(
                    name="AAPL",
                    type="stock",
                    asset_class=providers_schema.AssetClass.equities,
                    asset_type=providers_schema.AssetType.stock,
                    value_in_item_ccy=181.18,
                    units=1.0,
                    currency=core_schema.CurrencyCode.validate("USD"),
                ),
            ),
            call(
                linked_account_id=2,
                sub_account=providers_schema.Account(
                    id="acc-3",
                    name="Test account 3",
                    iso_currency=core_schema.CurrencyCode.validate("USD"),
                    type="brokerage",
                ),
                item=providers_schema.Asset(
                    name="LVMH",
                    type="stock",
                    asset_class=providers_schema.AssetClass.equities,
                    asset_type=providers_schema.AssetType.stock,
                    value_in_item_ccy=688.90,
                    units=1.0,
                    currency=core_schema.CurrencyCode.validate("EUR"),
                ),
            ),
        ]
    )


class TestXccyCollector:
    def test_all_currencies_are_collected(
        self,
        valid_snapshot_data: list[service.LinkedAccountSnapshotResult],
    ):
        collector = service.XccyCollector(target_ccy=TEST_USER_ACCOUNT_CCY)
        service.visit_snapshot_tree(valid_snapshot_data, collector)
        assert collector.xccys == {
            fx_market.Xccy("USD", TEST_USER_ACCOUNT_CCY),
            fx_market.Xccy("GBP", "USD"),
            fx_market.Xccy("EUR", "USD"),
        }
