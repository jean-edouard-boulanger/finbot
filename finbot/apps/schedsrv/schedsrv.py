from finbot.apps.schedsrv.request import Request
from finbot.apps.schedsrv.handler import RequestHandler
from finbot.clients import SnapClient, HistoryClient
from finbot.core import dbutils, tracer
from finbot.core.utils import configure_logging
from finbot.model import UserAccount
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from datetime import timedelta
from typing import List, Dict
import sys
import queue
import threading
import argparse
import stackprinter
import signal
import logging
import os
import zmq


configure_logging()
db_engine = create_engine(os.environ['FINBOT_DB_URL'])
db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))
tracer.configure(
    identity="schedsrv",
    persistence_layer=tracer.DBPersistenceLayer(db_session)
)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="valuation and reporting scheduler")
    parser.add_argument("--mode", choices={"server", "one_shot"}, type=str, default="server")
    parser.add_argument("--accounts", type=lambda v: set(int(i) for i in v.split(",")), default=None)
    return parser


def run_one_shot(handler: RequestHandler, accounts_ids: List[int]):
    for user_account in db_session.query(UserAccount).all():
        if not accounts_ids or user_account.id in accounts_ids:
            try:
                request = Request(user_account)
                handler.handle_valuation(request)
            except Exception as e:
                logging.warning(f"failure while running workflow for "
                                f"user_id={user_account.id}: {e}, "
                                f"trace: \n{stackprinter.format()}")


def pop_queue(work_queue: queue.Queue, timeout: timedelta):
    try:
        return work_queue.get(timeout=timeout.total_seconds())
    except queue.Empty:
        return None


class ValuationWorkerThread(threading.Thread):
    def __init__(self, session, work_queue: queue.Queue, request_handler: RequestHandler):
        super().__init__()
        self._session = session
        self._work_queue = work_queue
        self._handler = request_handler
        self._stop_event = threading.Event()

    def _consume(self, request: Request):
        try:
            logging.info(f"handling request: {request.serialize()}")
            self._handler.handle_valuation(request)
        except Exception as e:
            logging.warning(f"swallowed exception while handling valuation in worker thread: {e}")

    def run(self):
        logging.info("starting worker thread")
        while not self._stop_event.isSet():
            request: Request = pop_queue(self._work_queue, timeout=timedelta(seconds=1))
            if request is not None:
                self._consume(request)
        logging.info("worker thread going down now")

    def stop(self):
        logging.info("stopping worker thread")
        self._stop_event.set()


class WorkDispatcher(object):
    def __init__(self, work_queue: queue.Queue):
        self._queue = work_queue

    def dispatch(self, request: Request):
        self._queue.put(request)


class TriggerReceiver(object):
    def __init__(self, port):
        self._socket = zmq.Context().socket(zmq.PULL)
        self._socket.bind(f"tcp://*:{port}")

    def receive(self):
        events = self._socket.poll(timeout=1000)
        if not events:
            return None
        return self._socket.recv_json()


class TriggerListenerThread(threading.Thread):
    def __init__(self, receiver: TriggerReceiver, dispatcher: WorkDispatcher):
        super().__init__()
        self._receiver = receiver
        self._dispatcher = dispatcher
        self._stop_event = threading.Event()

    def run(self):
        logging.info("starting consumer thread")
        while not self._stop_event.isSet():
            data = self._receiver.receive()
            if data:
                request = Request.deserialize(data)
                self._dispatcher.dispatch(request)
        logging.info("consumer thread going down now")

    def stop(self):
        logging.info("stopping consumer thread")
        self._stop_event.set()


class StopHandler(object):
    def __init__(self, threads):
        self._threads = threads
        signal.signal(signal.SIGINT, self.handle_stop)
        signal.signal(signal.SIGTERM, self.handle_stop)

    def handle_stop(self, signum, frame):
        logging.info(f"received signal ({signum}), stopping all threads")
        [t.stop() for t in self._threads]


def main_impl():
    settings = create_parser().parse_args()

    snapwsrv_endpoint = os.environ["FINBOT_SNAPWSRV_ENDPOINT"]
    snap_client = SnapClient(snapwsrv_endpoint)
    logging.info(f"snapshot client created with {snapwsrv_endpoint} endpoint")

    histwsrv_endpoint = os.environ["FINBOT_HISTWSRV_ENDPOINT"]
    hist_client = HistoryClient(histwsrv_endpoint)
    logging.info(f"history report client created with {histwsrv_endpoint} endpoint")

    logging.info(f"running in mode: {settings.mode}")
    request_handler = RequestHandler(snap_client, hist_client)
    if settings.mode == "one_shot":
        run_one_shot(request_handler, settings.accounts)
        return

    schedsrv_port = int(os.environ["FINBOT_SCHEDSRV_PORT"])
    receiver = TriggerReceiver(schedsrv_port)
    logging.info(f"receiver listening on port {schedsrv_port}")

    threads = []
    work_queue = queue.Queue()
    worker_thread = ValuationWorkerThread(db_session, work_queue, request_handler)
    threads.append(worker_thread)

    dispatcher = WorkDispatcher(work_queue)
    consumer_thread = TriggerListenerThread(receiver, dispatcher)
    threads.append(consumer_thread)

    StopHandler(threads)

    [t.start() for t in threads]
    [t.join() for t in threads]


def main():
    try:
        main_impl()
        return 0
    except Exception:
        logging.error(f"fatal error while running schedsrv: \n{stackprinter.format()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
