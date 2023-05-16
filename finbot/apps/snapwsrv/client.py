from typing import Optional

from finbot.apps.snapwsrv import schema as snapwsrv_schema
from finbot.core.web_service import WebServiceClient


class SnapwsrvClient(WebServiceClient):
    service_name = "snapwsrv"

    def __init__(self, server_endpoint: str):
        super().__init__(server_endpoint)

    def take_snapshot(
        self,
        user_account_id: int,
        linked_account_ids: Optional[list[int]] = None,
    ) -> snapwsrv_schema.TakeSnapshotResponse:
        return snapwsrv_schema.TakeSnapshotResponse.parse_obj(
            self.post(
                f"snapshot/{user_account_id}/take/",
                snapwsrv_schema.TakeSnapshotRequest(
                    linked_account_ids=linked_account_ids
                ),
            )
        )
