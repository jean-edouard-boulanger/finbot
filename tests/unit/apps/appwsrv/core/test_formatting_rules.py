from finbot.providers.schema import AssetClass, AssetType
from finbot.apps.appwsrv.core.formatting_rules import (
    ASSET_CLASSES_FORMATTING_RULES,
    ASSET_TYPES_FORMATTING_RULES,
)


def test_all_asset_types_have_a_matching_rule():
    asset_types_with_a_rule = set(ASSET_TYPES_FORMATTING_RULES.keys())
    asset_types = set(asset_type for asset_type in AssetType)
    assert asset_types_with_a_rule == asset_types
    for asset_type, rule in ASSET_TYPES_FORMATTING_RULES.items():
        assert asset_type == rule.asset_type


def test_all_asset_classes_have_a_matching_rule():
    asset_classes_with_a_rule = set(ASSET_CLASSES_FORMATTING_RULES.keys())
    asset_classes = set(asset_class for asset_class in AssetClass)
    assert asset_classes_with_a_rule == asset_classes
    for asset_class, rule in ASSET_CLASSES_FORMATTING_RULES.items():
        assert asset_class == rule.asset_class
