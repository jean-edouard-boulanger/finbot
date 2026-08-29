import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from finbot.apps.appwsrv.events import event_hub
from finbot.core import environment, jwt
from finbot.core.events import Event, EventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Events"])

#: Subprotocol the client must offer and the server echoes back. Browsers cannot set an Authorization header
#: on a websocket, so the access token rides alongside this as a second subprotocol value.
SUBPROTOCOL = "finbot.events.v1"
BEARER_PREFIX = "bearer."

#: Close codes. 4401 mirrors HTTP 401; 4001 is a routine "your turn is up, reconnect".
CLOSE_UNAUTHORIZED = 4401
CLOSE_FORBIDDEN_ORIGIN = 4403
CLOSE_LIFETIME_REACHED = 4001

HEARTBEAT_INTERVAL_SECONDS = 30.0
#: Access tokens last a day. Capping the socket well short of that bounds how long a connection authenticated
#: by a since-invalidated token can survive; the client simply reconnects.
MAX_CONNECTION_SECONDS = 45 * 60.0


def _offered_protocols(websocket: WebSocket) -> list[str]:
    raw = websocket.headers.get("sec-websocket-protocol", "")
    return [value.strip() for value in raw.split(",") if value.strip()]


def _extract_token(protocols: list[str]) -> str | None:
    for protocol in protocols:
        if protocol.startswith(BEARER_PREFIX):
            return protocol[len(BEARER_PREFIX) :]
    return None


def _origin_allowed(websocket: WebSocket) -> bool:
    """Reject cross-site sockets.

    Browsers do not apply CORS to websockets, so this is the only thing standing between the bus and a page
    on another origin. Unlike the REST API (which stays safe under a wide-open CORS policy because an
    attacker page cannot forge the bearer token it never has), a browser will happily let another origin's
    page open this socket if we let it -- so this defaults to same-origin-only rather than mirroring the
    REST policy. `FINBOT_ALLOWED_WS_ORIGINS` is a comma-separated allowlist for deployments that legitimately
    serve the frontend from a different origin than the API.
    """
    origin = websocket.headers.get("origin")
    if origin is None:
        # Not a browser: there is no origin to lie about.
        return True
    parsed = urlparse(origin)
    origin_candidates = {origin, f"{parsed.scheme}://{parsed.hostname}"}
    allowed_raw = environment.get_environment_value_or("FINBOT_ALLOWED_WS_ORIGINS")
    if allowed_raw:
        allowed = {value.strip() for value in allowed_raw.split(",") if value.strip()}
        if origin_candidates & allowed:
            return True
    # Nothing configured, or no match: fall back to same-origin, so a same-origin deployment behind a
    # reverse proxy keeps working with zero configuration instead of silently allowing every origin.
    host = websocket.headers.get("host")
    return host is not None and parsed.netloc == host


@router.websocket("/ws")
async def events_websocket(websocket: WebSocket) -> None:
    """Stream events for the authenticated user.

    The socket is a hint channel, not a source of truth: it is best-effort, at-most-once, and every
    degradation path collapses to a `refetch` frame telling the client to re-read over REST.

    Keep in sync with webapp/src/contexts/events/events-stream.ts.
    """
    # Nothing may escape this function. The app registers exception handlers for AuthError and friends, and
    # Starlette's ExceptionMiddleware runs for websocket scopes too -- it would try to send an HTTP response
    # on a websocket scope and break the connection instead of closing it cleanly.
    try:
        protocols = _offered_protocols(websocket)
        if SUBPROTOCOL not in protocols:
            await websocket.close(code=CLOSE_UNAUTHORIZED)
            return
        if not _origin_allowed(websocket):
            logger.warning(f"rejected websocket from disallowed origin {websocket.headers.get('origin')!r}")
            await websocket.close(code=CLOSE_FORBIDDEN_ORIGIN)
            return
        token = _extract_token(protocols)
        if token is None:
            await websocket.close(code=CLOSE_UNAUTHORIZED)
            return
        try:
            user_account_id = int(jwt.verify_token(token, "access").sub)
        except Exception:
            await websocket.close(code=CLOSE_UNAUTHORIZED)
            return
        await websocket.accept(subprotocol=SUBPROTOCOL)
    except Exception:
        logger.exception("failed to establish events websocket")
        return

    queue = event_hub.subscribe(user_account_id)
    try:
        await _serve(websocket, queue, user_account_id)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception(f"events websocket failed for user_account_id={user_account_id}")
    finally:
        event_hub.unsubscribe(user_account_id, queue)
        try:
            await websocket.close()
        except Exception:
            logger.debug("events websocket already closed", exc_info=True)


async def _serve(websocket: WebSocket, queue: asyncio.Queue[Event], user_account_id: int) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + MAX_CONNECTION_SECONDS
    # Reading is what surfaces a client disconnect promptly; the frames themselves are not interesting.
    reader: asyncio.Future[Any] = asyncio.ensure_future(websocket.receive_text())
    pending_event: asyncio.Future[Any] = asyncio.ensure_future(queue.get())
    try:
        while True:
            timeout = min(HEARTBEAT_INTERVAL_SECONDS, max(0.0, deadline - loop.time()))
            done, _ = await asyncio.wait(
                {reader, pending_event},
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if reader in done:
                reader.result()  # raises WebSocketDisconnect once the client goes away
                reader = asyncio.ensure_future(websocket.receive_text())
            if pending_event in done:
                event: Event = pending_event.result()
                await websocket.send_text(event.model_dump_json())
                pending_event = asyncio.ensure_future(queue.get())
            if loop.time() >= deadline:
                await websocket.close(code=CLOSE_LIFETIME_REACHED)
                return
            if not done:
                await websocket.send_text(
                    Event(type=EventType.PING, user_account_id=user_account_id, seq=0).model_dump_json()
                )
    finally:
        for task in (reader, pending_event):
            task.cancel()
