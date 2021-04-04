from typing import Iterator, Optional, Any, TYPE_CHECKING
from contextlib import contextmanager
from functools import partial
import json

from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy import DateTime


if TYPE_CHECKING:
    from finbot.model import Base

    JSONEngine = TypeDecorator[Any]
else:
    JSONEngine = TypeDecorator


def add_persist_utilities(db_session: Any) -> Any:
    @contextmanager
    def persist(self: Any, entity: "Base") -> Iterator["Base"]:
        yield entity
        self.add(entity)
        self.commit()

    @contextmanager
    def persist_all(self: Any, entities: list["Base"]) -> Iterator[list["Base"]]:
        yield entities
        self.add_all(entities)
        self.commit()

    setattr(db_session, "persist", partial(persist, db_session))
    setattr(db_session, "persist_all", partial(persist_all, db_session))
    return db_session


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
