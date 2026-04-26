"""Tool framework — `ToolSpec`, `ToolResult`, and `@data_tool` / `@render_tool` decorators.

Each tool lives in its own module under `agent.tools.<name>`. A tool is declared by
applying `@data_tool(...)` or `@render_tool(...)` to a handler function:

    @data_tool(description="…", icon="wallet", label="…")
    def get_net_worth(session: SessionType, user_account_id: int, args: NoArgs) -> ToolResult:
        …

After decoration, the function symbol IS a `ToolSpec` (the original function is stored as
its `handler`). The decorator infers:
- `name` from the function's `__name__`
- `args_model` from the type annotation of the last parameter
- `is_render_tool` from which decorator was applied
"""

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar, get_type_hints

from finbot.apps.appwsrv.agent import schema as agent_schema
from finbot.core.schema import BaseModel
from finbot.model import SessionType

# ---------- Shared empty arg model ----------


class NoArgs(BaseModel):
    """Use as the args annotation for tools that take no parameters."""


# ---------- ToolResult ----------


@dataclass
class ToolResult:
    """Outcome of a tool invocation.

    `payload` is fed back to the LLM as JSON. `summary` is shown in the UI pill.
    `rich_block` is set ONLY by render tools — runner emits it as a `rich_block` SSE event.
    """

    payload: BaseModel | dict[str, Any]
    summary: str
    rich_block: agent_schema.RichBlock | None = field(default=None)

    def payload_json(self) -> str:
        if isinstance(self.payload, BaseModel):
            return self.payload.model_dump_json(exclude_none=True)
        import orjson

        return orjson.dumps(self.payload).decode()


# ---------- ToolSpec ----------


ArgsT = TypeVar("ArgsT", bound=BaseModel)
DataHandler = Callable[[SessionType, int, ArgsT], ToolResult]
RenderHandler = Callable[[ArgsT], ToolResult]
# Erased handler type used on `ToolSpec` — the runner dispatches on `is_render_tool`,
# so the field is intentionally arity-agnostic. Decorator call sites still receive the
# strict `DataHandler` / `RenderHandler` shapes.
AnyHandler = Callable[..., ToolResult]


@dataclass
class ToolSpec(Generic[ArgsT]):
    name: str
    description: str
    args_model: type[ArgsT]
    icon: str
    label: str
    is_render_tool: bool
    handler: AnyHandler

    def parameters_schema(self) -> dict[str, Any]:
        schema = self.args_model.model_json_schema()
        # Drop Pydantic noise that OpenAI doesn't need.
        schema.pop("title", None)
        return schema

    def to_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema(),
            },
        }


# ---------- Decorators ----------


def _extract_args_model(fn: Callable[..., Any], expected_param_count: int) -> type[BaseModel]:
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    if len(params) != expected_param_count:
        raise TypeError(f"@tool {fn.__name__}: expected {expected_param_count} parameters, got {len(params)}")
    args_param = params[-1]
    try:
        hints = get_type_hints(fn)
    except Exception as exc:  # pragma: no cover — would only fire for malformed annotations
        raise TypeError(f"@tool {fn.__name__}: failed to resolve type hints: {exc}") from exc
    annotation = hints.get(args_param.name)
    if not (isinstance(annotation, type) and issubclass(annotation, BaseModel)):
        raise TypeError(
            f"@tool {fn.__name__}: '{args_param.name}' must be annotated with a Pydantic BaseModel subclass"
        )
    return annotation


def data_tool(
    *,
    description: str,
    icon: str,
    label: str,
) -> Callable[[DataHandler[Any]], ToolSpec[Any]]:
    """Decorate a `(session, user_account_id, args) -> ToolResult` function as a data tool.

    The args model is inferred from the third parameter's type annotation.
    """

    def decorator(fn: DataHandler[Any]) -> ToolSpec[Any]:
        return ToolSpec(
            name=fn.__name__,
            description=description,
            args_model=_extract_args_model(fn, expected_param_count=3),
            icon=icon,
            label=label,
            is_render_tool=False,
            handler=fn,
        )

    return decorator


def render_tool(
    *,
    description: str,
    icon: str,
    label: str,
) -> Callable[[RenderHandler[Any]], ToolSpec[Any]]:
    """Decorate a `(args) -> ToolResult` function as a render tool.

    The args model is the rich-block shape the LLM emits; the runner picks it up
    from `result.rich_block` and forwards as a `rich_block` SSE event.
    """

    def decorator(fn: RenderHandler[Any]) -> ToolSpec[Any]:
        return ToolSpec(
            name=fn.__name__,
            description=description,
            args_model=_extract_args_model(fn, expected_param_count=1),
            icon=icon,
            label=label,
            is_render_tool=True,
            handler=fn,
        )

    return decorator
