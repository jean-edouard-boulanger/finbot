from contextlib import contextmanager
from functools import partial


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
