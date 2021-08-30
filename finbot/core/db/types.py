from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy import DateTime

from typing import Optional, Any, TYPE_CHECKING
import json


if TYPE_CHECKING:
    JSONEngine = TypeDecorator[Any]
else:
    JSONEngine = TypeDecorator


class JSONEncoded(JSONEngine):
    impl = VARCHAR

    def process_bind_param(self, value: Optional[Any], dialect: Any) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[Any]:
        if value is None:
            return None
        return json.loads(value)


DateTimeTz = DateTime(timezone=True)
