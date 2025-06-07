import asyncio
from functools import partial
from typing import AsyncIterable, Awaitable, Callable, ParamSpec, TypeVar, cast

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


async def aexec(func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
    impl = partial(func, *args, **kwargs)
    return await asyncio.get_running_loop().run_in_executor(None, impl)


async def acollect(async_it: AsyncIterable[T]) -> list[T]:
    return [v async for v in async_it]


async def maybe_awaitable(v: Awaitable[T] | T) -> T:
    if asyncio.iscoroutine(v):
        return cast(T, await v)
    return cast(T, v)
