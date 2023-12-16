import os
from unittest.mock import patch

import pytest

from finbot.core import environment


def test_get_environment_value():
    with patch.dict(os.environ, {"SOME_KEY": "SOME_VALUE"}, clear=True):
        assert environment.get_environment_value("SOME_KEY") == "SOME_VALUE"


def test_get_environment_value_or_returns_default():
    with patch.dict(os.environ, {}, clear=True):
        assert environment.get_environment_value_or("SOME_MISSING_KEY", "SOME_DEFAULT_VALUE") == "SOME_DEFAULT_VALUE"


def test_get_environment_value_or_returns_none_by_default():
    with patch.dict(os.environ, {}, clear=True):
        assert environment.get_environment_value_or("SOME_MISSING_KEY") is None


def test_get_environment_value_raises_when_variable_is_missing():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(environment.MissingEnvironment):
            environment.get_environment_value("SOME_MISSING_KEY_2")


@pytest.mark.parametrize(
    "environ_mock,expected_runtime",
    [
        ({}, environment.PRODUCTION_ENV),
        ({"FINBOT_ENV": environment.PRODUCTION_ENV}, environment.PRODUCTION_ENV),
        ({"FINBOT_ENV": "bad_value"}, environment.PRODUCTION_ENV),
        ({"FINBOT_ENV": environment.DEVELOPMENT_ENV}, environment.DEVELOPMENT_ENV),
    ],
)
def test_get_finbot_runtime(environ_mock: dict[str, str], expected_runtime: str):
    with patch.dict(os.environ, environ_mock, clear=True):
        assert environment.get_finbot_runtime() == expected_runtime
