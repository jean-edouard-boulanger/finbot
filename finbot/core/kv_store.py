from typing import Any, Optional, Protocol, Type, TypeVar, Union

from sqlalchemy.exc import NoResultFound  # type: ignore

from finbot.core.db.session import Query, Session
from finbot.core.serialization import serialize
from finbot.model import GenericKeyValueStore


class KVEntity(Protocol):
    key: str

    def serialize(self) -> Any:
        ...

    @staticmethod
    def deserialize(data: Any) -> "KVEntity":
        ...


T = TypeVar("T", bound=KVEntity)


class KVStore(Protocol):
    def __getitem__(self, key: str) -> Any:
        ...

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        ...

    def get_entity(self, entity_type: Type[T]) -> Optional[T]:
        ...

    def __setitem__(self, key: str, value: Any) -> None:
        ...

    def set_entity(self, entity: T) -> None:
        ...

    def __delitem__(self, key: str) -> None:
        ...

    def delete_entity(self, entity: Union[T, Type[T]]) -> None:
        ...

    def __contains__(self, key: str) -> bool:
        ...

    def has_entity(self, entity_type: Union[T, Type[T]]) -> bool:
        ...


class DBKVStore(KVStore):
    class _NoDefault(object):
        pass

    def __init__(self, session: Session):
        self._session = session

    def __query(self, key: str) -> Query[GenericKeyValueStore]:
        query: Query[GenericKeyValueStore] = self._session.query(
            GenericKeyValueStore
        ).filter_by(key=key)
        return query

    def __getitem__(self, key: str) -> Any:
        return self.get(key, default=DBKVStore._NoDefault)

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        try:
            item: GenericKeyValueStore = self.__query(key).one()
            return item.value
        except NoResultFound:
            if default is DBKVStore._NoDefault:
                raise KeyError(key)
            return default

    def get_entity(self, entity_type: Type[T]) -> Optional[T]:
        data = self.get(entity_type.key)
        if data is None:
            return None
        return entity_type.deserialize(data)  # type: ignore

    def __setitem__(self, key: str, value: Any) -> None:
        self._session.merge(GenericKeyValueStore(key=key, value=value))
        self._session.commit()

    def set_entity(self, entity: T) -> None:
        self[entity.key] = serialize(entity)

    def __delitem__(self, key: str) -> None:
        self.__query(key).delete()
        self._session.commit()

    def delete_entity(self, entity: Union[T, Type[T]]) -> None:
        del self[entity.key]

    def __contains__(self, key: str) -> bool:
        return self.__query(key).count() > 0

    def has_entity(self, entity_type: Union[T, Type[T]]) -> bool:
        return entity_type.key in self
