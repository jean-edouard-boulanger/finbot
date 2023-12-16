import pytest

from finbot.apps.appwsrv.client import AppwsrvClient


@pytest.fixture
def api() -> AppwsrvClient:
    return AppwsrvClient.create()


def test_healthy(api: AppwsrvClient):
    assert api.healthy
