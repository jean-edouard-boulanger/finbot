from finbot.clients import WorkerClient, ValuationRequest
from finbot.core import tracer, environment
from finbot.core.errors import FinbotError
from finbot.core.logging import configure_logging
from finbot.core.db.session import Session
from finbot.core.utils import format_stack
from finbot.model import UserAccount

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import schedule

from typing import Iterable
from datetime import timedelta
import sys
import queue
import threading
import argparse
import signal
import logging


FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)

db_engine = create_engine(FINBOT_ENV.database_url)
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))
tracer.configure(
    identity="schedsrv", persistence_layer=tracer.DBPersistenceLayer(db_session)
)


def parse_valuation_requests(raw_accounts_str: str):
    requests = []
    raw_accounts = raw_accounts_str.split(";")
    for raw_account in raw_accounts:
        if ":" in raw_account:
            account_id_str, linked_accounts_str = raw_account.split(":")
            request = ValuationRequest(
                user_account_id=int(account_id_str),
                linked_accounts=[
                    int(linked_account_id_str)
                    for linked_account_id_str in linked_accounts_str.split(",")
                ],
            )
        else:
            request = ValuationRequest(user_account_id=int(raw_account))
        requests.append(request)
    return requests


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="valuation and reporting scheduler")
    parser.add_argument(
        "--mode", choices={"server", "one_shot"}, type=str, default="server"
    )
    parser.add_argument("--accounts", type=parse_valuation_requests, default=None)
    return parser


def iter_user_accounts():
    for user_account in db_session.query(UserAccount).all():
        yield user_account


def run_one_shot(requests: Iterable[ValuationRequest]):
    for request in requests:
        try:
            worker_client = WorkerClient()
            logging.info(f"handling valuation request {request}")
            valuation = worker_client.get_valuation(request)
            logging.info(
                f"user account {request.user_account_id} valuation"
                f" (linked_accounts={request.linked_accounts}): {valuation.dict()}"
            )
        except Exception as e:
            logging.warning(
                f"failure while running workflow for "
                f"user_id={request.user_account_id}: {e}, "
                f"trace: \n{format_stack()}"
            )


def pop_queue(work_queue: queue.Queue, timeout: timedelta):
    try:
        return work_queue.get(timeout=timeout.total_seconds())
    except queue.Empty:
        return None


class SchedulerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self._scheduler = schedule.Scheduler()
        self._stop_event = threading.Event()
        self._scheduler.every().day.at("08:00").do(self._dispatch_valuation)
        self._scheduler.every().day.at("13:00").do(self._dispatch_valuation)
        self._scheduler.every().day.at("18:00").do(self._dispatch_valuation)

    def _dispatch_valuation(self) -> None:
        logging.info("[scheduler thread] dispatching valuation for all accounts")
        user_account: UserAccount
        for user_account in iter_user_accounts():
            user_account_id = user_account.id
            logging.info(
                f"[scheduler thread] dispatching valuation for user_account_id={user_account_id}"
            )
            worker_client = WorkerClient()
            worker_client.trigger_valuation(
                ValuationRequest(user_account_id=user_account_id)
            )

    def run(self) -> None:
        logging.info("[scheduler thread] starting")
        while not self._stop_event.is_set():
            self._scheduler.run_pending()
            logging.info(
                f"[scheduler thread] sleeping {self._scheduler.idle_seconds}s "
                f"until next job at {self._scheduler.next_run.isoformat()}"
            )
            self._stop_event.wait(self._scheduler.idle_seconds)
        logging.info("[scheduler thread] going down now")

    def stop(self):
        logging.info("[scheduler thread] stop requested")
        self._stop_event.set()


class StopHandler(object):
    def __init__(self, threads):
        self._threads = threads
        signal.signal(signal.SIGINT, self.handle_stop)
        signal.signal(signal.SIGTERM, self.handle_stop)

    def handle_stop(self, signum, frame):
        logging.info(f"received signal ({signum}), stopping all worker threads")
        [t.stop() for t in self._threads]


def main_impl():
    settings = create_parser().parse_args()

    logging.info(f"running in mode: {settings.mode}")
    if settings.mode == "one_shot":
        if settings.accounts is None:
            raise FinbotError("--accounts must be provided in on shot mode")
        run_one_shot(settings.accounts)
        return

    threads = []

    logging.info("initializing scheduler thread")
    scheduler_thread = SchedulerThread()
    threads.append(scheduler_thread)

    StopHandler(threads)

    logging.info("starting all worker threads")
    [t.start() for t in threads]

    logging.info("scheduler service is ready")
    [t.join() for t in threads]


def main():
    try:
        main_impl()
        return 0
    except Exception:
        logging.error(f"fatal error while running schedsrv: \n{format_stack()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
