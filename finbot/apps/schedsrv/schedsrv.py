from finbot.clients import WorkerClient, ValuationRequest
from finbot.core import tracer, environment
from finbot.core.logging import configure_logging
from finbot.core.db.session import Session
from finbot.core.utils import format_stack
from finbot.model import UserAccount

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import schedule

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


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="valuation and reporting scheduler")
    parser.add_argument(
        "--mode", choices={"server", "one_shot"}, type=str, default="server"
    )
    parser.add_argument(
        "--accounts", type=lambda v: set(int(i) for i in v.split(",")), default=None
    )
    return parser


def iter_user_accounts():
    for user_account in db_session.query(UserAccount).all():
        yield user_account


def run_one_shot(accounts_ids: list[int]):
    user_account: UserAccount
    for user_account in iter_user_accounts():
        if not accounts_ids or user_account.id in accounts_ids:
            try:
                worker_client = WorkerClient()
                valuation = worker_client.get_valuation(
                    ValuationRequest(user_account_id=user_account.id)
                )
                logging.info(
                    f"user account {user_account.id} valuation {valuation.dict()}"
                )
            except Exception as e:
                logging.warning(
                    f"failure while running workflow for "
                    f"user_id={user_account.id}: {e}, "
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

    def _dispatch_valuation(self):
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
