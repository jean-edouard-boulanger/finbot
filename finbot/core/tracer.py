from finbot.model import DistributedTrace
from typing import ContextManager, List, Optional, Dict
from datetime import datetime
import stackprinter
import contextlib
import threading
import uuid
import logging


CONTEXT_TAG = "__tracer_context__"


class Step(object):
    def __init__(self,
                 guid: str,
                 path: List[int],
                 name: str,
                 start_time: datetime,
                 metadata: Dict = None):
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


class DBPersistenceLayer(object):
    def __init__(self, db_session):
        self.db_session = db_session

    def persist(self, step):
        dt = DistributedTrace(
            guid=step.guid,
            path=step.pretty_path,
            name=step.name,
            user_data=step.metadata,
            start_time=step.start_time,
            end_time=step.end_time)
        self.db_session.merge(dt)
        self.db_session.commit()


class NoopPersistenceLayer(object):
    def persist(self, step: Step):
        pass


class FlatContext(object):
    def __init__(self, guid: str, path: List[int]):
        self.guid = guid
        self.path = path

    def serialize(self):
        return {
            "guid": self.guid,
            "path": self.path
        }


def _dummy_step() -> Step:
    return Step(guid=str(), path=[], name="dummy", start_time=datetime.now())


class TracerContext(object):
    def __init__(self, persistence_layer):
        self._persistence_layer = persistence_layer
        self._steps: List[Step] = []
        self._path: List[int] = []

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
            Step(guid=flat_context.guid,
                 path=flat_context.path,
                 name=name,
                 start_time=datetime.now())
        ]
        step = self._steps[-1]
        self._persistence_layer.persist(step)
        logging.info(f"adopted tracer context name='{step.name}' guid={step.guid} path={step.pretty_path}")
        return step

    def new_root(self, name):
        self._path = [0, 0]
        self._steps = [
            Step(guid=str(uuid.uuid4()),
                 path=self._path[:-1],
                 name=name,
                 start_time=datetime.now())
        ]
        step = self._steps[-1]
        self._persistence_layer.persist(step)
        logging.info(f"new tracer root name='{step.name}' guid={step.guid} path={step.pretty_path}")
        return step

    def new_child(self, name):
        if not self.has_root():
            return _dummy_step()
        self._steps.append(
            Step(guid=self._steps[0].guid,
                 path=self._path[:],
                 name=name,
                 start_time=datetime.now())
        )
        step = self._steps[-1]
        self._persistence_layer.persist(step)
        logging.info(f"new tracer child name='{step.name}' guid={step.guid} path={step.pretty_path}")
        self._path += [0]
        return self._steps[-1]

    def unwind(self):
        if not self.has_root():
            return
        self._path.pop()
        step = self._steps.pop()
        step.end_time = datetime.now()
        self._persistence_layer.persist(step)
        if len(self._steps) == 0:
            self._steps = []
            self._path = []
            return
        self._path[-1] += 1

    def current(self) -> Step:
        if not self.has_root():
            return _dummy_step()
        return self._steps[-1]


def _get_persistence_layer():
    return _get_persistence_layer.layer


_get_persistence_layer.layer = NoopPersistenceLayer()


def set_persistence_layer(layer):
    _get_persistence_layer.layer = layer


def _get_tracer_context() -> TracerContext:
    tls = _get_tracer_context.tls
    tracer_context = getattr(tls, "tracer_context", None)
    if not tracer_context:
        tls.tracer_context = TracerContext(_get_persistence_layer())
    return tls.tracer_context


_get_tracer_context.tls = threading.local()


@contextlib.contextmanager
def adopt(flat_context: FlatContext, name: str) -> ContextManager[Step]:
    context = _get_tracer_context()
    step = context.adopt(flat_context, name)
    try:
        yield step
    finally:
        context.unwind()
        assert not context.has_root()


@contextlib.contextmanager
def root(name: str) -> ContextManager[Step]:
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
def sub_step(name: str) -> ContextManager[Step]:
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


def propagate() -> FlatContext:
    return _get_tracer_context().propagate()
