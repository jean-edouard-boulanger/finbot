from typing import Generic, TypeAlias, TypeVar

T = TypeVar("T")


class _JSONSerialized(Generic[T]):
    pass


JSON: TypeAlias = None | bool | str | float | int | list["JSON"] | dict[str, "JSON"]
JSONSerialized: TypeAlias = JSON | _JSONSerialized[T]
