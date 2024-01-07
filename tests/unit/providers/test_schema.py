import pytest

from finbot.providers import schema
from finbot.core.schema import CurrencyCode


def test_asset_init_fails_when_both_value_in_account_ccy_and_value_in_item_ccy_are_specified():
    with pytest.raises(ValueError):
        schema.Asset(
            name="AAPL",
            type="stock",
            asset_class=schema.AssetClass.equities,
            asset_type=schema.AssetType.stock,
            value_in_account_ccy=1000.0,
            value_in_item_ccy=1000.0,
            units=3.0,
            currency=CurrencyCode.validate("USD"),
        )


def test_asset_init_fails_when_value_in_item_ccy_is_specified_but_ccy_is_missing():
    with pytest.raises(ValueError):
        schema.Asset(
            name="AAPL",
            type="stock",
            asset_class=schema.AssetClass.equities,
            asset_type=schema.AssetType.stock,
            value_in_item_ccy=1000.0,
            units=3.0,
        )


def test_asset_init_fails_when_no_value_is_specified():
    with pytest.raises(ValueError):
        schema.Asset(
            name="AAPL",
            type="stock",
            asset_class=schema.AssetClass.equities,
            asset_type=schema.AssetType.stock,
            units=3.0,
        )


def test_liability_init_fails_when_both_value_in_account_ccy_and_value_in_item_ccy_are_specified():
    with pytest.raises(ValueError):
        schema.Liability(
            name="Credit card",
            type="credit",
            value_in_account_ccy=1000.0,
            value_in_item_ccy=1000.0,
            currency=CurrencyCode.validate("USD"),
        )


def test_liability_init_fails_when_value_in_item_ccy_is_specified_but_ccy_is_missing():
    with pytest.raises(ValueError):
        schema.Liability(
            name="Credit card",
            type="credit",
            value_in_item_ccy=1000.0,
        )


def test_liability_init_fails_when_no_value_is_specified():
    with pytest.raises(ValueError):
        schema.Asset(
            name="Credit card",
            type="credit",
        )
