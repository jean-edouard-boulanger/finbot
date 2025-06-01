import pytest
from pydantic import ValidationError

from finbot.core.schema import CurrencyCode
from finbot.providers import schema


def test_asset_init_fails_when_both_value_in_account_ccy_and_value_in_item_ccy_are_specified():
    with pytest.raises(ValidationError):
        schema.Asset(
            name="AAPL",
            type="stock",
            asset_class=schema.AssetClass.equities,
            asset_type=schema.AssetType.stock,
            value_in_account_ccy=1000.0,
            value_in_item_ccy=1100.0,
            units=3.0,
            currency=CurrencyCode("USD"),
        )


def test_asset_init_fails_when_no_value_is_specified():
    with pytest.raises(ValidationError):
        schema.Asset(
            name="AAPL",
            type="stock",
            asset_class=schema.AssetClass.equities,
            asset_type=schema.AssetType.stock,
            units=3.0,
            currency=CurrencyCode("USD"),
        )


def test_liability_init_fails_when_both_value_in_account_ccy_and_value_in_item_ccy_are_specified():
    with pytest.raises(ValidationError):
        schema.Liability(
            name="Credit card",
            type="credit",
            value_in_account_ccy=2000.0,
            value_in_item_ccy=2100.0,
            currency=CurrencyCode("USD"),
        )


def test_liability_init_fails_when_no_value_is_specified():
    with pytest.raises(ValidationError):
        schema.Liability(
            name="Credit card",
            type="credit",
            currency=CurrencyCode("USD"),
        )


@pytest.mark.parametrize("account_type", schema.AccountType)
def test_account_init_fails_when_invalid_sub_type_is_specified(
    account_type: schema.AccountType,
):
    with pytest.raises(ValidationError):
        schema.Account(
            id="TEST_ACC_1",
            name="Test Account 1",
            iso_currency=CurrencyCode("USD"),
            type=account_type,
            sub_type="bad_account_sub_type",
        )
