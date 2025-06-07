import contextlib
import threading
from contextvars import ContextVar, Token
from functools import wraps
from types import TracebackType
from typing import Any, Callable, Iterator, ParamSpec, TypeAlias, TypeVar, cast

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from finbot.core import environment

_SESSION_CTX = ContextVar("db_session", default=None)

P = ParamSpec("P")
R = TypeVar("R")


Base = declarative_base()
BaseT = TypeVar("BaseT", bound=Base)

SessionType: TypeAlias = Session


class SingletonEngine:
    _lock = threading.Lock()
    _inst = None

    @classmethod
    def get_instance(cls) -> Any:
        with cls._lock:
            if not cls._inst:
                cls._inst = create_engine(environment.get_database_url())
            return cls._inst


class ScopedSession:
    def __init__(self) -> None:
        self._tokens: list[Token[None]] = []

    def __enter__(self) -> SessionType:
        session = sessionmaker(bind=SingletonEngine.get_instance())()
        self._tokens.append(_SESSION_CTX.set(session))
        return cast(SessionType, session)

    def __exit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        session = cast(SessionType, _SESSION_CTX.get())
        assert session
        session.rollback()
        session.close()
        _SESSION_CTX.reset(self._tokens.pop(-1))


def with_scoped_session(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def impl(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    return impl


def get_current_session() -> SessionType:
    session = _SESSION_CTX.get()
    assert session, "Using database session outside context"
    return cast(SessionType, session)


class _Db:
    @property
    def session(self) -> SessionType:
        return get_current_session()

    @property
    def engine(self) -> Any:
        return SingletonEngine.get_instance()


db = _Db()


class PersistScope:
    def __init__(self, session: SessionType | None = None):
        self.__session = session

    @property
    def _session(self) -> SessionType:
        return self.__session or db.session

    @contextlib.contextmanager
    def __call__(self, item: BaseT) -> Iterator[BaseT]:
        try:
            yield item
            self._session.add(item)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise


@contextlib.contextmanager
def persist_scope(item: BaseT) -> Iterator[BaseT]:
    with PersistScope(db.session)(item):
        yield item
