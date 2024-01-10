import pytest

from finbot.core.pydantic_ import ValidationError
from finbot.providers import schema


def test_asset_init_fails_when_both_value_in_account_ccy_and_value_in_item_ccy_are_specified():
    with pytest.raises(ValidationError) as exc_info:
        schema.Asset(
            name="AAPL",
            type="stock",
            asset_class=schema.AssetClass.equities,
            asset_type=schema.AssetType.stock,
            value_in_account_ccy=1000.0,
            value_in_item_ccy=1100.0,
            units=3.0,
            currency="USD",
        )
    assert exc_info.value.errors() == [
        {
            "loc": ("__root__",),
            "msg": "Either `value_in_account_ccy` (1000.0) or `value_in_unit_ccy` (1100.0) must be set.",
            "type": "value_error",
        }
    ]


def test_asset_init_fails_when_no_value_is_specified():
    with pytest.raises(ValidationError) as exc_info:
        schema.Asset(
            name="AAPL",
            type="stock",
            asset_class=schema.AssetClass.equities,
            asset_type=schema.AssetType.stock,
            units=3.0,
            currency="USD",
        )
    assert exc_info.value.errors() == [
        {
            "loc": ("__root__",),
            "msg": "Either `value_in_account_ccy` (None) or `value_in_unit_ccy` (None) must be set.",
            "type": "value_error",
        }
    ]


def test_liability_init_fails_when_both_value_in_account_ccy_and_value_in_item_ccy_are_specified():
    with pytest.raises(ValidationError) as exc_info:
        schema.Liability(
            name="Credit card",
            type="credit",
            value_in_account_ccy=2000.0,
            value_in_item_ccy=2100.0,
            currency="USD",
        )
    assert exc_info.value.errors() == [
        {
            "loc": ("__root__",),
            "msg": "Either `value_in_account_ccy` (2000.0) or `value_in_unit_ccy` (2100.0) must be set.",
            "type": "value_error",
        }
    ]


def test_liability_init_fails_when_no_value_is_specified():
    with pytest.raises(ValidationError) as exc_info:
        schema.Liability(
            name="Credit card",
            type="credit",
            currency="EUR",
        )
    assert exc_info.value.errors() == [
        {
            "loc": ("__root__",),
            "msg": "Either `value_in_account_ccy` (None) or `value_in_unit_ccy` (None) must be set.",
            "type": "value_error",
        }
    ]


@pytest.mark.parametrize("account_type", schema.AccountType)
def test_account_init_fails_when_invalid_sub_type_is_specified(
    account_type: schema.AccountType,
):
    with pytest.raises(ValidationError) as exc_info:
        schema.Account(
            id="TEST_ACC_1",
            name="Test Account 1",
            iso_currency="EUR",
            type=account_type,
            sub_type="bad_account_sub_type",
        )
    valid_values = schema.VALID_ACCOUNT_SUB_TYPES[account_type]
    assert exc_info.value.errors() == [
        {
            "loc": ("__root__",),
            "msg": f"'bad_account_sub_type' is not a valid '{account_type.value}' account sub-type."
            f" Valid values are: {', '.join(str(v) for v in valid_values)}.",
            "type": "value_error",
        }
    ]
