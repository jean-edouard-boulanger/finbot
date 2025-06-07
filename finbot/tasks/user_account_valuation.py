import logging

from finbot.core.typing_extensions import JSONSerialized
from finbot.model import ScopedSession
from finbot.services.user_account_snapshot import UserAccountSnapshotService
from finbot.services.user_account_valuation import (
    UserAccountValuationService,
    ValuationRequest,
    ValuationResponse,
)
from finbot.services.valuation_history_writer import ValuationHistoryWriterService
from finbot.tasks.base import Client, celery_app

logger = logging.getLogger(__name__)


@celery_app.task()  # type: ignore
def user_account_valuation_task(
    serialized_request: JSONSerialized[ValuationRequest],
) -> JSONSerialized[ValuationResponse]:
    with ScopedSession() as session:
        service = UserAccountValuationService(
            db_session=session,
            user_account_snapshot_service=UserAccountSnapshotService(session),
            valuation_history_writer_service=ValuationHistoryWriterService(session),
        )
        request = ValuationRequest.model_validate(serialized_request)
        return service.process_valuation(request).model_dump()


client = Client[ValuationRequest, ValuationResponse](user_account_valuation_task, ValuationRequest, ValuationResponse)
