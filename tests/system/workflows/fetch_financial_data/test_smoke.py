import pytest

from finbot.core.environment import get_secret_key
from finbot.core.secure import fernet_encrypt_json
from finbot.core.temporal_ import GENERIC_TASK_QUEUE, TRY_ONCE, get_temporal_client, temporal_workflow_id
from finbot.providers import schema as providers_schema
from finbot.providers.dummy_uk import make_default_dummy_data
from finbot.workflows.fetch_financial_data import schema as finbotwsrv_schema
from finbot.workflows.fetch_financial_data.workflows import GetFinancialDataWorkflow


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


@pytest.mark.asyncio
async def test_get_financial_data():
    client = await get_temporal_client()
    user_account_currency = providers_schema.CurrencyCode("EUR")
    response = await client.execute_workflow(
        GetFinancialDataWorkflow,
        finbotwsrv_schema.GetFinancialDataRequest(
            provider_id="dummy_uk",
            encrypted_credentials=fernet_encrypt_json(
                {
                    "dummy_data": make_default_dummy_data(user_account_currency, sub_accounts_count=1).model_dump(),
                },
                get_secret_key(),
            ).decode(),
            items=[
                finbotwsrv_schema.LineItem.Assets,
                finbotwsrv_schema.LineItem.Accounts,
            ],
            user_account_currency=user_account_currency,
        ),
        id=temporal_workflow_id(prefix="tests/system/"),
        retry_policy=TRY_ONCE,
        task_queue=GENERIC_TASK_QUEUE,
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
