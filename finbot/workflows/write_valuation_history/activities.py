from temporalio import activity

from finbot.workflows.write_valuation_history import schema


@activity.defn(name="write_history")
def write_history(
    request: schema.WriteHistoryRequest,
) -> schema.WriteHistoryResponse:
    from finbot.model import ScopedSession
    from finbot.workflows.write_valuation_history.service import ValuationHistoryWriterService

    with ScopedSession() as session:
        return ValuationHistoryWriterService(session).write_history(request)
