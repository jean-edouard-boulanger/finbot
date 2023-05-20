import logging

from finbot.core.typing_extensions import JSONSerialized
from finbot.services.user_account_snapshot import UserAccountSnapshotService
from finbot.services.user_account_valuation import (
    UserAccountValuationService,
    ValuationRequest,
    ValuationResponse,
)
from finbot.services.valuation_history_writer import ValuationHistoryWriterService
from finbot.tasks.base import Client, celery_app, db_session

logger = logging.getLogger(__name__)


@celery_app.task()  # type: ignore
def user_account_valuation_task(
    serialized_request: JSONSerialized[ValuationRequest],
) -> JSONSerialized[ValuationResponse]:
    service = UserAccountValuationService(
        db_session=db_session,
        user_account_snapshot_service=UserAccountSnapshotService(db_session),
        valuation_history_writer_service=ValuationHistoryWriterService(db_session),
    )
    request = ValuationRequest.parse_obj(serialized_request)
    return service.process_valuation(request).dict()


client = Client[ValuationRequest, ValuationResponse](
    user_account_valuation_task, ValuationRequest, ValuationResponse
)
