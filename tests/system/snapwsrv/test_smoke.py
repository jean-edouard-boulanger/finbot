from finbot.apps.snapwsrv.client import SnapwsrvClient
import pytest


@pytest.fixture
def api() -> SnapwsrvClient:
    return SnapwsrvClient.create()


def test_healthy(api: SnapwsrvClient):
    assert api.healthy
