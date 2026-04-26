from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from finbot.apps.appwsrv.agent import schema as agent_schema
from finbot.apps.appwsrv.agent.runner import stream_agent_response
from finbot.apps.http_base import CurrentUserIdDep, ORJSONResponse
from finbot.core.environment import get_openai_api_key

router = APIRouter(prefix="/chat", tags=["Chat assistant"])


@router.post("/", operation_id="chat")
async def chat(
    request: agent_schema.ChatRequest,
    current_user_id: CurrentUserIdDep,
) -> StreamingResponse:
    """Stream a chat response as Server-Sent Events.

    Stateless: the client posts the full prior history with each request. The server
    does not persist conversations.
    """
    if not get_openai_api_key():
        return ORJSONResponse(  # type: ignore[return-value]
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            content={
                "error": "feature_unavailable",
                "user_message": "Chat assistant is not configured on this server",
            },
        )
    return StreamingResponse(
        stream_agent_response(current_user_id, request.messages),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
