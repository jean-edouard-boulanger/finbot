from typing import Any, cast


def row_to_dict(row: Any) -> dict[str, Any]:
    return cast(dict[str, Any], row._asdict())
