from unittest.mock import patch
import pytest
import os

from finbot.core.environment import get_environment_value, MissingEnvironment


def test_get_environment_value():
    with patch.dict(os.environ, {"SOME_KEY": "SOME_VALUE"}, clear=True):
        assert get_environment_value("SOME_KEY") == "SOME_VALUE"


def test_get_environment_value_returns_default():
    with patch.dict(os.environ, {}, clear=True):
        assert (
            get_environment_value("SOME_MISSING_KEY", "SOME_DEFAULT_VALUE")
            == "SOME_DEFAULT_VALUE"
        )


def test_get_environment_value_raises_when_variable_is_missing():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(MissingEnvironment):
            get_environment_value("SOME_MISSING_KEY_2")
