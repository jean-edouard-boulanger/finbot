from typing import Optional, Any, Union
from datetime import datetime, date
import dataclasses
import decimal
import json


def serialize(data: Any) -> Any:
    def serialize_key(key: Any) -> Optional[Union[str, int, float, bool]]:
        if key is None:
            return key
        if not isinstance(key, (str, int, float, bool)):
            return str(key)
        return key

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
    if dataclasses.is_dataclass(data):
        return serialize(dataclasses.asdict(data))
    return data


def pretty_dump(data: Any) -> str:
    def fallback(unhandled_data: Any) -> str:
        return f"<not serializable {type(unhandled_data)} {unhandled_data}>"

    return json.dumps(serialize(data), indent=4, default=fallback)
