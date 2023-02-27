import pydantic

from typing import Optional, Any, Union, TypeVar
from datetime import datetime, date
import dataclasses
import decimal
import json


T = TypeVar("T")


def serialize(data: Any) -> Any:
    def serialize_key(key: Any) -> Optional[Union[str, int, float, bool]]:
        if key is None:
            return key
        if not isinstance(key, (str, int, float, bool)):
            return str(key)
        return key

    if isinstance(data, pydantic.BaseModel):
        return serialize(data.dict())
    if dataclasses.is_dataclass(data):
        return serialize(dataclasses.asdict(data))
    if hasattr(data, "serialize"):
        return serialize(data.serialize())
    if isinstance(data, decimal.Decimal):
        return float(data)
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    if isinstance(data, dict):
        return {serialize_key(k): serialize(v) for k, v in data.items()}
    if isinstance(data, (list, set, tuple)):
        return [serialize(v) for v in data]
    if isinstance(data, bytes):
        return data.decode()
    return data


def pretty_dump(data: Any, **json_override_kwarg: Any) -> str:
    def fallback(unhandled_data: Any) -> str:
        return f"<not serializable {type(unhandled_data)} {unhandled_data}>"

    json_kwargs = {"indent": 4, "default": fallback, **json_override_kwarg}
    return json.dumps(serialize(data), **json_kwargs)  # type: ignore
