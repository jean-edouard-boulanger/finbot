from finbot.apps.histwsrv.client import HistwsrvClient
import pytest


@pytest.fixture
def api() -> HistwsrvClient:
    return HistwsrvClient.create()


def test_healthy(api: HistwsrvClient):
    assert api.healthy
