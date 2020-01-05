from sqlalchemy.types import TypeDecorator, VARCHAR
from contextlib import contextmanager
from functools import partial
from sqlalchemy import DateTime
import json


def add_persist_utilities(db_session):
    @contextmanager
    def persist(self, entity):
        yield entity
        self.add(entity)
        self.commit()

    @contextmanager
    def persist_all(self, entities):
        yield entities
        self.add_all(entities)
        self.commit()

    db_session.persist = partial(persist, db_session)
    db_session.persist_all = partial(persist_all, db_session)
    return db_session


class JSONEncoded(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


DateTimeTz = DateTime(timezone=True)
