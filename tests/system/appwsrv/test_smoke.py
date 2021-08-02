from finbot.core.environment import get_appwsrv_endpoint
from finbot.clients.app import AppClient
import pytest


@pytest.fixture
def api() -> AppClient:
    return AppClient(get_appwsrv_endpoint())


def test_healthy(api: AppClient):
    assert api.healthy
