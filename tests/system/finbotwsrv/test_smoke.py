import pytest

from finbot.apps.finbotwsrv import schema as finbotwsrv_schema
from finbot.apps.finbotwsrv.client import FinbotwsrvClient
from finbot.providers import schema as providers_schema


@pytest.fixture
def api() -> FinbotwsrvClient:
    return FinbotwsrvClient.create()


def test_healthy(api: FinbotwsrvClient):
    assert api.healthy


def check_account(account: providers_schema.Account):
    assert account.id == "dummy"
    assert account.iso_currency == "GBP"
    assert account.type == "cash"


def check_assets_financial_data(results: list[providers_schema.AssetsEntry]):
    assert len(results) == 1
    assets_entry = results[0]
    check_account(assets_entry.account)
    assets = assets_entry.assets
    assert len(assets) == 1
    asset = assets[0]
    assert asset.name == "GBP"
    assert asset.type == "currency"
    assert asset.asset_class == "foreign_currency"
    assert asset.asset_type == "cash"
    assert asset.value == 1000.0


def check_balances_financial_data(results: list[providers_schema.BalanceEntry]):
    assert len(results) == 1
    balances_entry = results[0]
    check_account(balances_entry.account)
    assert balances_entry.balance == 1000.0


def test_get_financial_data(api: FinbotwsrvClient):
    response = api.get_financial_data(
        provider_id="dummy_uk",
        credentials_data={},
        line_items=[
            finbotwsrv_schema.LineItem.Assets,
            finbotwsrv_schema.LineItem.Balances,
        ],
        user_account_currency=providers_schema.CurrencyCode("EUR"),
    )
    financial_data = response.financial_data
    assert len(financial_data) == 2
    for entry in financial_data:
        if isinstance(entry, finbotwsrv_schema.AssetsResults):
            assert entry.line_item == finbotwsrv_schema.LineItem.Assets
            check_assets_financial_data(entry.results)
        elif isinstance(entry, finbotwsrv_schema.BalancesResults):
            assert entry.line_item == finbotwsrv_schema.LineItem.Balances
            check_balances_financial_data(entry.results)
        else:
            raise AssertionError(f"Unexpected entry: {entry}")
