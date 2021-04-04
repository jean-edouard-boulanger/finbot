from finbot.model import DistributedTrace
from typing import Iterator, List, Optional, Dict
from datetime import datetime
import stackprinter
import contextlib
import threading
import uuid
import logging
import os


CONTEXT_TAG = "__tracer_context__"


class Config(object):
    def __init__(self, identity=None, persistence_layer=None):
        self.identity = identity
        self.persistence_layer = persistence_layer


class Step(object):
    def __init__(
        self,
        guid: str,
        path: List[int],
        name: str,
        start_time: datetime,
        metadata: Dict = None,
    ):
        self._guid = guid
        self._path = path
        self._start_time = start_time
        self._name = name
        self.metadata = metadata or {}
        self.end_time: Optional[datetime] = None

    def set_output(self, data):
        self.metadata["output"] = data

    def set_failure(self, message):
        self.metadata["error"] = message

    def set_origin(self, origin):
        self.metadata["origin"] = origin

    def set_pid(self, pid):
        self.metadata["pid"] = pid

    def set_description(self, description):
        self.metadata["description"] = description

    @property
    def guid(self) -> str:
        return self._guid

    @property
    def pretty_path(self) -> str:
        return ".".join(str(c) for c in self._path)

    @property
    def path(self):
        return self._path

    @property
    def start_time(self):
        return self._start_time

    @property
    def name(self):
        return self._name


class FlatContext(object):
    def __init__(self, guid: str, path: List[int]):
        self.guid = guid
        self.path = path

    def serialize(self):
        return {"guid": self.guid, "path": self.path}


def _dummy_step() -> Step:
    return Step(guid=str(), path=[], name="dummy", start_time=datetime.now())


class ThreadLogFilter(logging.Filter):
    def __init__(self, thread_name):
        super().__init__()
        self.thread_name = thread_name

    def filter(self, record):
        return record.threadName == self.thread_name


class ExcludeFileLogFilter(logging.Filter):
    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name

    def filter(self, record):
        return record.filename != self.file_name


class LogHandler(logging.StreamHandler):
    def __init__(self, step_accessor):
        super().__init__()
        self._step_accessor = step_accessor

    def emit(self, record):
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
        self._steps: List[Step] = []
        self._path: List[int] = []

    def _new_step(self, guid, path, name):
        step = Step(guid=guid, path=path, name=name, start_time=datetime.now())
        step.set_origin(self._config.identity)
        step.set_pid(os.getpid())
        return step

    def has_root(self) -> bool:
        return len(self._steps) > 0

    def propagate(self) -> Optional[FlatContext]:
        if not self.has_root():
            return None
        flat_context = FlatContext(guid=self._steps[0].guid, path=list(self._path))
        self._path[-1] += 1
        return flat_context

    def adopt(self, flat_context: Optional[FlatContext], name: str):
        if flat_context is None:
            return _dummy_step()
        self._path = flat_context.path + [0]
        self._steps = [
            self._new_step(guid=flat_context.guid, path=flat_context.path, name=name)
        ]
        step = self._steps[-1]
        self._config.persistence_layer.persist(step)
        logging.info(
            f"adopted tracer context name='{step.name}' guid={step.guid} path={step.pretty_path}"
        )
        return step

    def new_root(self, name):
        self._path = [0, 0]
        self._steps = [
            self._new_step(guid=str(uuid.uuid4()), path=self._path[:-1], name=name)
        ]
        step = self._steps[-1]
        self._config.persistence_layer.persist(step)
        logging.info(
            f"new tracer root name='{step.name}' guid={step.guid} path={step.pretty_path}"
        )
        return step

    def new_child(self, name):
        if not self.has_root():
            return _dummy_step()
        self._steps.append(
            self._new_step(guid=self._steps[0].guid, path=self._path[:], name=name)
        )
        step = self._steps[-1]
        self._config.persistence_layer.persist(step)
        logging.info(
            f"new tracer child name='{step.name}' guid={step.guid} path={step.pretty_path}"
        )
        self._path += [0]
        return self._steps[-1]

    def unwind(self):
        if not self.has_root():
            return
        self._path.pop()
        step = self._steps.pop()
        step.end_time = datetime.now()
        self._config.persistence_layer.persist(step)
        if len(self._steps) == 0:
            self._steps = []
            self._path = []
            return
        self._path[-1] += 1

    def current(self) -> Step:
        if not self.has_root():
            return _dummy_step()
        return self._steps[-1]


class DBPersistenceLayer(object):
    def __init__(self, db_session):
        self.db_session = db_session

    def persist(self, step: Step):
        dt = DistributedTrace(
            guid=step.guid,
            path=step.pretty_path,
            name=step.name,
            user_data=step.metadata,
            start_time=step.start_time,
            end_time=step.end_time,
        )
        self.db_session.merge(dt)
        self.db_session.commit()


class NoopPersistenceLayer(object):
    def persist(self, step: Step):
        pass


class _Singleton(object):
    def __init__(self):
        self.config: Config = Config(persistence_layer=NoopPersistenceLayer)
        self.tls = threading.local()


_SINGLETON = _Singleton()


def _get_config() -> Config:
    return _SINGLETON.config


def configure(identity=None, persistence_layer=None):
    _SINGLETON.config = Config(
        identity=identity, persistence_layer=persistence_layer or NoopPersistenceLayer()
    )


def _get_tracer_context() -> TracerContext:
    tls = _SINGLETON.tls
    tracer_context: Optional[TracerContext] = getattr(tls, "tracer_context", None)
    if not tracer_context:
        tls.tracer_context = TracerContext(_get_config())
        log_handler = LogHandler(current)
        log_handler.addFilter(ThreadLogFilter(threading.current_thread().name))
        log_handler.addFilter(ExcludeFileLogFilter(os.path.basename(__file__)))
        logging.getLogger().addHandler(log_handler)
    return tls.tracer_context


@contextlib.contextmanager
def adopt(flat_context: FlatContext, name: str) -> Iterator[Step]:
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


def current() -> Step:
    return _get_tracer_context().current()


def propagate() -> Optional[FlatContext]:
    return _get_tracer_context().propagate()
