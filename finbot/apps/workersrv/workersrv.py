from typing import Any

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from finbot.apps.workersrv import schema
from finbot.apps.workersrv.valuation_handler import ValuationHandler
from finbot.clients import HistoryClient, SnapClient
from finbot.core import environment
from finbot.core.db.session import Session
from finbot.core.logging import configure_logging

FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)

db_engine = create_engine(FINBOT_ENV.database_url)
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))


worker = Celery("celery_app", backend="rpc://", broker=FINBOT_ENV.rmq_url)
worker.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)


@worker.task()  # type: ignore
def handle_healthy() -> bool:
    return True


@worker.task()  # type: ignore
def handle_valuation_request(serialized_request: dict[str, Any]) -> dict[str, Any]:
    handler = ValuationHandler(
        db_session=db_session,
        snap_client=SnapClient(FINBOT_ENV.snapwsrv_endpoint),
        hist_client=HistoryClient(FINBOT_ENV.histwsrv_endpoint),
    )
    request = schema.ValuationRequest.parse_obj(serialized_request)
    return handler.handle_valuation(request).dict()
