from finbot.apps.histwsrv import schema as histwsrv_schema
from finbot.core.web_service import WebServiceClient


class HistwsrvClient(WebServiceClient):
    service_name = "histwsrv"

    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def write_history(self, snapshot_id: int) -> histwsrv_schema.WriteHistoryResponse:
        return histwsrv_schema.WriteHistoryResponse.parse_obj(
            self.post(f"history/{snapshot_id}/write/")
        )