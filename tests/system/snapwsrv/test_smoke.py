from finbot.core.environment import get_snapwsrv_endpoint
from finbot.clients import SnapClient
import pytest


@pytest.fixture
def api() -> SnapClient:
    return SnapClient(get_snapwsrv_endpoint())


def test_healthy(api: SnapClient):
    assert api.healthy
