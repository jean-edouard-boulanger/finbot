from finbot.model import DistributedTrace
from finbot.core.utils import serialize

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session
from typing import Iterator, Optional, Protocol, TypedDict, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from logging import LogRecord
import stackprinter
import contextlib
import threading
import uuid
import logging
import os


CONTEXT_TAG = "__tracer_context__"


class Step(object):
    def __init__(
        self,
        guid: str,
        path: list[int],
        name: str,
        start_time: datetime,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self._guid = guid
        self._path = path
        self._start_time = start_time
        self._name = name
        self.metadata = metadata or {}
        self.end_time: Optional[datetime] = None

    def set_input(self, data: Any) -> None:
        self.metadata["input"] = data

    def set_output(self, data: Any) -> None:
        self.metadata["output"] = data

    def set_failure(self, message: str) -> None:
        self.metadata["error"] = message

    def set_origin(self, origin: str) -> None:
        self.metadata["origin"] = origin

    def set_pid(self, pid: int) -> None:
        self.metadata["pid"] = pid

    def set_description(self, description: str) -> None:
        self.metadata["description"] = description

    @property
    def is_root(self) -> bool:
        return len(self.path) == 1

    @property
    def parent_path(self) -> Optional[list[int]]:
        return None if self.is_root else self.path[:-1]

    @property
    def guid(self) -> str:
        return self._guid

    @property
    def pretty_path(self) -> str:
        return ".".join(str(c) for c in self._path)

    @property
    def path(self) -> list[int]:
        return self._path

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def name(self) -> str:
        return self._name


class PersistenceLayer(Protocol):
    def persist(self, step: Step) -> None:
        pass


class DBPersistenceLayer(PersistenceLayer):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def _persist(self, step: Step) -> None:
        dt = DistributedTrace(
            guid=step.guid,
            path=step.pretty_path,
            name=step.name,
            user_data=serialize(step.metadata),
            start_time=step.start_time,
            end_time=step.end_time,
        )
        self.db_session.merge(dt)
        self.db_session.commit()

    def persist(self, step: Step) -> None:
        try:
            self._persist(step)
        except SQLAlchemyError as e:
            logging.warning(f"failed to persist step '{step.name}': {e}")
            self.db_session.rollback()


class NoopPersistenceLayer(PersistenceLayer):
    def persist(self, step: Step) -> None:
        pass


@dataclass
class Config:
    identity: str
    persistence_layer: PersistenceLayer


class SerializedFlatContext(TypedDict):
    guid: str
    path: list[int]


@dataclass
class FlatContext(object):
    guid: str
    path: list[int]

    def serialize(self) -> SerializedFlatContext:
        return {"guid": self.guid, "path": self.path}


def _dummy_step() -> Step:
    return Step(guid=str(), path=[], name="dummy", start_time=datetime.now())


class ThreadLogFilter(logging.Filter):
    def __init__(self, thread_name: str):
        super().__init__()
        self.thread_name = thread_name

    def filter(self, record: LogRecord) -> bool:
        return record.threadName == self.thread_name


class ExcludeFileLogFilter(logging.Filter):
    def __init__(self, file_name: str):
        super().__init__()
        self.file_name = file_name

    def filter(self, record: LogRecord) -> bool:
        return record.filename != self.file_name


class LogHandler(logging.StreamHandler):
    def __init__(self, step_accessor: Callable[[], Step]):
        super().__init__()
        self._step_accessor = step_accessor

    def emit(self, record: LogRecord) -> None:
        step = self._step_accessor()
        step.metadata.setdefault("logs", []).append(
            {
                "time": record.asctime,
                "level": record.levelname,
                "filename": record.filename,
                "line": record.lineno,
                "function": record.funcName,
                "message": record.message,
                "thread": record.threadName,
            }
        )


class TracerContext(object):
    def __init__(self, config: Config):
        self._config = config
        self._steps: list[Step] = []
        self._path: list[int] = []

    def _new_step(self, guid: str, path: list[int], name: str) -> Step:
        step = Step(guid=guid, path=path, name=name, start_time=datetime.now())
        step.set_origin(self._config.identity)
        step.set_pid(os.getpid())
        return step

    def _safe_persist(self, step: Step) -> None:
        try:
            self._config.persistence_layer.persist(step)
        except Exception as e:
            logging.warning(f"failed to persist step {step.name}: {e}")

    def has_root(self) -> bool:
        return len(self._steps) > 0

    def propagate(self) -> Optional[FlatContext]:
        if not self.has_root():
            return None
        flat_context = FlatContext(guid=self._steps[0].guid, path=list(self._path))
        self._path[-1] += 1
        return flat_context

    def adopt(self, flat_context: Optional[FlatContext], name: str) -> Step:
        if flat_context is None:
            return _dummy_step()
        self._path = flat_context.path + [0]
        self._steps = [
            self._new_step(guid=flat_context.guid, path=flat_context.path, name=name)
        ]
        step = self._steps[-1]
        self._safe_persist(step)
        logging.info(
            f"adopted tracer context name='{step.name}' guid={step.guid} path={step.pretty_path}"
        )
        return step

    def new_root(self, name: str) -> Step:
        self._path = [0, 0]
        self._steps = [
            self._new_step(guid=str(uuid.uuid4()), path=self._path[:-1], name=name)
        ]
        step = self._steps[-1]
        self._safe_persist(step)
        logging.info(
            f"new tracer root name='{step.name}' guid={step.guid} path={step.pretty_path}"
        )
        return step

    def new_child(self, name: str) -> Step:
        if not self.has_root():
            return _dummy_step()
        self._steps.append(
            self._new_step(guid=self._steps[0].guid, path=self._path[:], name=name)
        )
        step = self._steps[-1]
        self._safe_persist(step)
        logging.info(
            f"new tracer child name='{step.name}' guid={step.guid} path={step.pretty_path}"
        )
        self._path += [0]
        return self._steps[-1]

    def unwind(self) -> None:
        if not self.has_root():
            return
        self._path.pop()
        step = self._steps.pop()
        step.end_time = datetime.now()
        self._safe_persist(step)
        if len(self._steps) == 0:
            self._steps = []
            self._path = []
            return
        self._path[-1] += 1

    def current(self) -> Step:
        if not self.has_root():
            return _dummy_step()
        return self._steps[-1]

    def guid(self) -> Optional[str]:
        if not self.has_root():
            return None
        return self._steps[0].guid


class _Singleton(object):
    def __init__(self) -> None:
        self.config: Config = Config(
            identity="default", persistence_layer=NoopPersistenceLayer()
        )
        self.tls = threading.local()


_SINGLETON = _Singleton()


def _get_config() -> Config:
    return _SINGLETON.config


def configure(identity: str, persistence_layer: PersistenceLayer) -> None:
    _SINGLETON.config = Config(
        identity=identity, persistence_layer=persistence_layer or NoopPersistenceLayer()
    )


def _get_tracer_context() -> TracerContext:
    tls = _SINGLETON.tls
    tracer_context: Optional[TracerContext] = getattr(tls, "tracer_context", None)
    if not tracer_context:
        tracer_context = TracerContext(_get_config())
        log_handler = LogHandler(current)
        log_handler.addFilter(ThreadLogFilter(threading.current_thread().name))
        log_handler.addFilter(ExcludeFileLogFilter(os.path.basename(__file__)))
        logging.getLogger().addHandler(log_handler)
        tls.tracer_context = tracer_context
    assert isinstance(tracer_context, TracerContext)
    return tracer_context


@contextlib.contextmanager
def adopt(flat_context: Optional[FlatContext], name: str) -> Iterator[Step]:
    context = _get_tracer_context()
    step = context.adopt(flat_context, name)
    try:
        yield step
    finally:
        context.unwind()
        assert not context.has_root()


@contextlib.contextmanager
def root(name: str) -> Iterator[Step]:
    context = _get_tracer_context()
    step = context.new_root(name)
    try:
        yield step
    except Exception:
        step.set_failure(stackprinter.format())
        raise
    finally:
        context.unwind()
        assert not context.has_root()


@contextlib.contextmanager
def sub_step(name: str) -> Iterator[Step]:
    context = _get_tracer_context()
    step = context.new_child(name)
    try:
        yield step
    except Exception:
        step.set_failure(stackprinter.format())
        raise
    finally:
        context.unwind()


def milestone(name: str, **kwargs: Any) -> None:
    with sub_step(name) as step:
        for key, value in kwargs.items():
            step.metadata[key] = value


def current() -> Step:
    return _get_tracer_context().current()


def propagate() -> Optional[FlatContext]:
    return _get_tracer_context().propagate()


def context_identifier() -> Optional[str]:
    return _get_tracer_context().guid()


def pack_context(request: dict[Any, Any], context: Optional[FlatContext]) -> dict[Any, Any]:
    if context:
        request[CONTEXT_TAG] = context.serialize()
    return request


@dataclass
class TreeNode:
    path: tuple[int, ...]
    data: DistributedTrace
    children: list["TreeNode"] = field(default_factory=list)
    extra_properties: dict[str, Any] = field(default_factory=dict)

    def serialize(self) -> dict[str, Any]:
        return {
            "path": self.data.path,
            "name": self.data.name,
            "metadata": self.data.user_data,
            "start_time": self.data.start_time,
            "end_time": self.data.end_time,
            "children": [child.serialize() for child in self.children],
            "extra_properties": self.extra_properties,
        }


def _get_parent_path(path: tuple[int, ...]) -> Optional[tuple[int, ...]]:
    if len(path) <= 1:
        return None
    return path[:-1]


def _back_propagate_error(
    node: TreeNode, mapped_nodes: dict[tuple[int, ...], TreeNode]
) -> None:
    if node.extra_properties["error_state"] != "self":
        return
    current_node = node
    while parent_path := _get_parent_path(current_node.path):
        parent_node = mapped_nodes.get(parent_path)
        if not parent_node:
            return
        if parent_node.extra_properties["error_state"] != "self":
            parent_node.extra_properties["error_state"] = "inherit"
        current_node = parent_node


def build_tree(traces: list[DistributedTrace]) -> TreeNode:
    tree = None
    mapped_nodes: dict[tuple[int, ...], TreeNode] = {}
    for trace in traces:
        pretty_path = tuple([int(val) for val in trace.path.split(".")])
        is_root = len(pretty_path) == 1
        assert isinstance(trace.user_data, dict)
        is_error = trace.user_data.get("error") is not None
        node = TreeNode(
            pretty_path,
            trace,
            extra_properties={"error_state": "self" if is_error else None},
        )
        mapped_nodes[pretty_path] = node
        if is_root == 1:
            if tree is not None:
                raise ValueError("invalid trace: found multiple roots")
            tree = node
    if tree is None:
        raise ValueError("invalid trace: no root found")
    for node in mapped_nodes.values():
        if node is tree:
            continue
        parent_path = _get_parent_path(node.path)
        assert parent_path is not None
        parent_node = mapped_nodes.get(parent_path)
        if parent_node:
            parent_node.children.append(node)
            _back_propagate_error(node, mapped_nodes)
    return tree
