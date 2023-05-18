import logging

from finbot.services.user_account_valuation import ValuationResponse, ValuationRequest, UserAccountValuationService
from finbot.apps.histwsrv.client import HistwsrvClient
from finbot.apps.snapwsrv.client import SnapwsrvClient
from finbot.core.typing_extensions import JSONSerialized
from finbot.tasks.base import Client, celery_app, db_session

logger = logging.getLogger(__name__)


@celery_app.task()  # type: ignore
def user_account_valuation_task(
    serialized_request: JSONSerialized[ValuationRequest],
) -> JSONSerialized[ValuationResponse]:
    service = UserAccountValuationService(
        db_session=db_session,
        snap_client=SnapwsrvClient.create(),
        hist_client=HistwsrvClient.create(),
    )
    request = ValuationRequest.parse_obj(serialized_request)
    return service.process_valuation(request).dict()


client = Client[ValuationRequest, ValuationResponse](
    user_account_valuation_task, ValuationRequest, ValuationResponse
)
