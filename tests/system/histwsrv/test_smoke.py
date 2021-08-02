from finbot.core.environment import get_histwsrv_endpoint
from finbot.clients import HistoryClient
import pytest


@pytest.fixture
def api() -> HistoryClient:
    return HistoryClient(get_histwsrv_endpoint())


def test_healthy(api: HistoryClient):
    assert api.healthy
