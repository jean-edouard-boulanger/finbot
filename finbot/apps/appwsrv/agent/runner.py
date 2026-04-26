"""Streaming agent runner — drives the OpenAI tool-call loop and emits SSE events.

The chat endpoint is stateless: the client posts the full conversation history each
turn. This generator opens its own DB session because FastAPI's `manage_db_session`
middleware closes its session before the StreamingResponse body runs.
"""

import json
import logging
from typing import Any, AsyncIterator, cast

import orjson
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

from finbot.apps.appwsrv.agent import schema as agent_schema
from finbot.apps.appwsrv.agent import tools as agent_tools
from finbot.apps.appwsrv.agent.prompts import build_system_prompt
from finbot.core.environment import get_environment_value_or, get_openai_api_key
from finbot.model import ScopedSession

logger = logging.getLogger(__name__)


CHAT_MODEL: str = get_environment_value_or("FINBOT_CHAT_MODEL") or "gpt-5.5"
MAX_ROUNDS: int = 8


def _sse(event: str, payload: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {orjson.dumps(payload).decode()}\n\n".encode()


async def stream_agent_response(
    user_account_id: int,
    messages: list[agent_schema.ChatMessage],
) -> AsyncIterator[bytes]:
    api_key = get_openai_api_key()
    if not api_key:
        # Caller (route) should have returned 503 already; double-guard.
        yield _sse("error", {"message": "Chat assistant is not configured on this server"})
        yield _sse("done", {})
        return

    with ScopedSession() as session:
        try:
            system_prompt = build_system_prompt(session, user_account_id)
        except Exception as exc:
            logger.exception("failed to build system prompt for user %s", user_account_id)
            yield _sse("error", {"message": f"Failed to load context: {exc}"})
            yield _sse("done", {})
            return

        oa_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *[{"role": m.role, "content": m.content} for m in messages],
        ]
        client = AsyncOpenAI(api_key=api_key)

        yield _sse("assistant_message_start", {})

        for _round in range(MAX_ROUNDS):
            try:
                stream = await client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=cast(list[ChatCompletionMessageParam], oa_messages),
                    tools=cast(list[ChatCompletionToolParam], agent_tools.OPENAI_TOOLS),
                    stream=True,
                )
            except Exception as exc:
                logger.exception("OpenAI request failed")
                yield _sse("error", {"message": f"Chat request failed: {exc}"})
                break

            text_acc = ""
            tool_acc: dict[int, dict[str, str]] = {}
            finish_reason: str | None = None

            try:
                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    choice = chunk.choices[0]
                    delta = choice.delta
                    if delta.content:
                        text_acc += delta.content
                        yield _sse("text_delta", {"delta": delta.content})
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            slot = tool_acc.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                            if tc.id:
                                slot["id"] = tc.id
                            fn = tc.function
                            if fn is not None:
                                if fn.name:
                                    slot["name"] = fn.name
                                if fn.arguments:
                                    slot["args"] += fn.arguments
                    if choice.finish_reason:
                        finish_reason = choice.finish_reason
            except Exception as exc:
                logger.exception("OpenAI stream interrupted")
                yield _sse("error", {"message": f"Chat stream interrupted: {exc}"})
                break

            assistant_msg: dict[str, Any] = {"role": "assistant"}
            if text_acc:
                assistant_msg["content"] = text_acc
            if tool_acc:
                assistant_msg["tool_calls"] = [
                    {
                        "id": s["id"],
                        "type": "function",
                        "function": {"name": s["name"], "arguments": s["args"] or "{}"},
                    }
                    for s in tool_acc.values()
                ]
            oa_messages.append(assistant_msg)

            if finish_reason != "tool_calls" or not tool_acc:
                break

            for slot in tool_acc.values():
                spec = agent_tools.TOOLS_BY_NAME.get(slot["name"])
                try:
                    args = json.loads(slot["args"] or "{}")
                except json.JSONDecodeError:
                    args = {}

                if spec is None:
                    yield _sse(
                        "tool_call_end",
                        {"id": slot["id"], "status": "error", "result_summary": f"unknown tool: {slot['name']}"},
                    )
                    oa_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": slot["id"],
                            "content": f"ERROR: unknown tool {slot['name']!r}",
                        }
                    )
                    continue

                yield _sse(
                    "tool_call_start",
                    {
                        "id": slot["id"],
                        "name": spec.name,
                        "label": spec.label,
                        "icon": spec.icon,
                    },
                )

                try:
                    parsed_args = spec.args_model.model_validate(args)
                    if spec.is_render_tool:
                        result = spec.handler(parsed_args)
                    else:
                        result = spec.handler(session, user_account_id, parsed_args)
                except Exception as exc:
                    logger.exception("tool %s failed", spec.name)
                    yield _sse(
                        "tool_call_end",
                        {"id": slot["id"], "status": "error", "result_summary": str(exc)[:120]},
                    )
                    oa_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": slot["id"],
                            "content": f"ERROR: {exc}",
                        }
                    )
                    continue

                if result.rich_block is not None:
                    yield _sse("rich_block", {"block": result.rich_block.model_dump()})

                yield _sse(
                    "tool_call_end",
                    {"id": slot["id"], "status": "done", "result_summary": result.summary},
                )
                oa_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": slot["id"],
                        "content": result.payload_json(),
                    }
                )
        else:
            yield _sse(
                "text_delta",
                {"delta": "I had trouble completing that — could you rephrase?"},
            )

        yield _sse("done", {})
