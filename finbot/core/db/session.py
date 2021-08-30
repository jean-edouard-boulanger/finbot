from finbot.model import Base

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.query import Query as SQLAlchemyQuery
from sqlalchemy.orm.session import Session as SQLAlchemySession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.types import TypeDecorator

from typing import TypeVar, Type, Generic, Any, Union, Iterator, TYPE_CHECKING
from contextlib import contextmanager


if TYPE_CHECKING:
    JSONEngine = TypeDecorator[Any]
    Query = SQLAlchemyQuery
else:
    JSONEngine = TypeDecorator
    T = TypeVar("T")

    class Query(Generic[T]):
        pass


SessionBase = TypeVar("SessionBase", bound=Union[SQLAlchemySession, scoped_session])

Entity = TypeVar("Entity", bound=Base)


class Session(object):
    def __init__(self, impl: SessionBase):
        self._impl = impl

    def delete(self, entity: Entity) -> None:
        self._impl.delete(entity)  # type: ignore

    def add(self, entity: Entity) -> None:
        self._impl.add(entity)

    def add_all(self, entities: list[Entity]) -> None:
        self._impl.add_all(entities)

    def merge(self, instance: Entity, load: bool = True) -> Entity:
        return self._impl.merge(instance, load)

    def query(self, entity: Type[Entity]) -> Query:  # type: ignore
        return self._impl.query(entity)

    def commit(self) -> None:
        self._impl.commit()

    def rollback(self) -> None:
        return self._impl.rollback()

    def close(self) -> None:
        self._impl.close()

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        return self._impl.execute(*args, **kwargs)

    def remove(self) -> None:
        self._impl.remove()

    @contextmanager
    def begin(self, nested: bool = False) -> Iterator["Session"]:
        with self._impl.begin(nested=nested) as impl_child:
            yield Session(impl_child)

    @contextmanager
    def begin_nested(self) -> Iterator["Session"]:
        with self._impl.begin_nested() as impl_child:
            yield Session(impl_child)

    @contextmanager
    def persist(self, entity: Entity) -> Iterator[Entity]:
        try:
            yield entity
            self.add(entity)
            self.commit()
        except SQLAlchemyError:
            self.rollback()
            raise

    @contextmanager
    def persist_all(self, entities: list[Entity]) -> Iterator[list[Entity]]:
        try:
            yield entities
            self.add_all(entities)
            self.commit()
        except SQLAlchemyError:
            self.rollback()
            raise
