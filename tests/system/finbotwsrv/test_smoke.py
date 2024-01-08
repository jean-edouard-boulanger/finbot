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
    assert account.type == "depository"
    assert account.sub_type == "checking"


def check_assets_financial_data(results: list[providers_schema.AssetsEntry]):
    assert len(results) == 1
    assets_entry = results[0]
    assert assets_entry.account_id == "dummy"
    assets = assets_entry.items
    assert len(assets) == 1
    asset = assets[0]
    assert asset.name == "GBP"
    assert asset.type == "currency"
    assert asset.asset_class == "foreign_currency"
    assert asset.asset_type == "cash"
    assert asset.value_in_item_ccy == 1000.0
    assert asset.value_in_account_ccy is None


def check_accounts_financial_data(results: list[providers_schema.Account]):
    assert len(results) == 1
    check_account(results[0])


def test_get_financial_data(api: FinbotwsrvClient):
    response = api.get_financial_data(
        provider_id="dummy_uk",
        credentials_data={},
        line_items=[
            finbotwsrv_schema.LineItem.Assets,
            finbotwsrv_schema.LineItem.Accounts,
        ],
        user_account_currency=providers_schema.CurrencyCode("EUR"),
    )
    financial_data = response.financial_data
    assert len(financial_data) == 2
    for entry in financial_data:
        if isinstance(entry, finbotwsrv_schema.AssetsResults):
            assert entry.line_item == finbotwsrv_schema.LineItem.Assets
            check_assets_financial_data(entry.results)
        elif isinstance(entry, finbotwsrv_schema.AccountsResults):
            assert entry.line_item == finbotwsrv_schema.LineItem.Accounts
            check_accounts_financial_data(entry.results)
        else:
            raise AssertionError(f"Unexpected entry: {entry}")
