from functools import partial
from pytz import timezone
from datetime import datetime
from contextlib import contextmanager
import json


def pretty_dump(data):
    return json.dumps(data, indent=4)


def now_utc():
    return datetime.now(timezone('UTC'))


def improve_session(db_session):
    @contextmanager
    def persist(self, entity):
        try:
            yield entity
        finally:
            self.add(entity)
            self.commit()

    @contextmanager
    def persist_all(self, entities):
        try:
            yield entities
        finally:
            self.add_all(entities)
            self.commit()

    db_session.persist = partial(persist, db_session)
    db_session.persist_all = partial(persist_all, db_session)
    return db_session
