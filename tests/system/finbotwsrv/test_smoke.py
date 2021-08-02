from finbot.core.environment import get_finbotwsrv_endpoint
from finbot.clients.finbot import FinbotClient, LineItem
import pytest


@pytest.fixture
def api() -> FinbotClient:
    return FinbotClient(get_finbotwsrv_endpoint())


def test_healthy(api: FinbotClient):
    assert api.healthy


def check_account(data):
    assert data["id"] == "dummy"
    assert data["iso_currency"] == "GBP"
    assert data["type"] == "cash"


def check_assets_financial_data(results):
    assert len(results) == 1
    data = results[0]
    check_account(data["account"])
    assets = data["assets"]
    assert len(assets) == 1
    asset = assets[0]
    assert asset["name"] == "Cash"
    assert asset["type"] == "currency"
    assert asset["value"] == 1000.0


def check_balances_financial_data(results):
    assert len(results) == 1
    data = results[0]
    check_account(data["account"])
    assert data["balance"] == 1000.0


def test_get_financial_data(api: FinbotClient):
    response = api.get_financial_data(
        provider="dummy_uk",
        credentials_data={},
        line_items=[
            LineItem.Assets,
            LineItem.Balances,
        ]
    )
    assert "financial_data" in response
    financial_data = response["financial_data"]
    print(financial_data)
    assert len(financial_data) == 2
    for entry in financial_data:
        line_item = entry["line_item"]
        if line_item == "assets":
            check_assets_financial_data(entry["results"])
        elif line_item == "balances":
            check_balances_financial_data(entry["results"])
        else:
            assert False, f"Unexpected line item: {line_item}"
