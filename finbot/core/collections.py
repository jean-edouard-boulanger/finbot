from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")


def drop_dict_items_with_null_values(d: dict[K, V | None]) -> dict[K, V]:
    return {k: v for (k, v) in d.items() if v is not None}
