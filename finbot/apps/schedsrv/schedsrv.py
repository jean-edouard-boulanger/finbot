import abc
import argparse
import logging
import signal
import sys
import threading
import traceback
from types import FrameType
from typing import Generator, Iterable

import schedule
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from finbot.core import environment
from finbot.core.db.session import Session
from finbot.core.errors import FinbotError
from finbot.core.logging import configure_logging
from finbot.model import UserAccount
from finbot.tasks import user_account_valuation

FINBOT_ENV = environment.get()
configure_logging(FINBOT_ENV.desired_log_level)

db_engine = create_engine(FINBOT_ENV.database_url)
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))


class Worker(abc.ABC, threading.Thread):
    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def stop(self) -> None:
        pass


def parse_valuation_requests(
    raw_accounts_str: str,
) -> list[user_account_valuation.ValuationRequest]:
    requests = []
    raw_accounts = raw_accounts_str.split(";")
    for raw_account in raw_accounts:
        if ":" in raw_account:
            account_id_str, linked_accounts_str = raw_account.split(":")
            request = user_account_valuation.ValuationRequest(
                user_account_id=int(account_id_str),
                linked_accounts=[
                    int(linked_account_id_str)
                    for linked_account_id_str in linked_accounts_str.split(",")
                ],
            )
        else:
            request = user_account_valuation.ValuationRequest(
                user_account_id=int(raw_account)
            )
        requests.append(request)
    return requests


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="valuation and reporting scheduler")
    parser.add_argument(
        "--mode", choices={"server", "one_shot"}, type=str, default="server"
    )
    parser.add_argument("--accounts", type=parse_valuation_requests, default=None)
    return parser


def iter_user_accounts() -> Generator[UserAccount, None, None]:
    for user_account in db_session.query(UserAccount).all():
        yield user_account


def run_one_shot(requests: Iterable[user_account_valuation.ValuationRequest]) -> None:
    for request in requests:
        try:
            logging.info(f"handling valuation request {request}")
            valuation = user_account_valuation.client.run(request)
            logging.info(
                f"user account {request.user_account_id} valuation"
                f" (linked_accounts={request.linked_accounts}): {valuation.dict()}"
            )
        except Exception as e:
            logging.warning(
                f"failure while running workflow for "
                f"user_id={request.user_account_id}: {e}, "
                f"trace: \n{traceback.format_exc()}"
            )


class Scheduler(Worker):
    def __init__(self) -> None:
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
            user_account_valuation.client.run_async(
                user_account_valuation.ValuationRequest(user_account_id=user_account_id)
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

    def stop(self) -> None:
        logging.info("[scheduler thread] stop requested")
        self._stop_event.set()


class StopHandler(object):
    def __init__(self, workers: list[Worker]) -> None:
        self._workers = workers
        signal.signal(signal.SIGINT, self.handle_stop)
        signal.signal(signal.SIGTERM, self.handle_stop)

    def handle_stop(self, signum: int, _: FrameType | None) -> None:
        logging.info(f"received signal ({signum}), stopping all workers")
        for worker in self._workers:
            worker.stop()


def main_impl() -> None:
    settings = create_parser().parse_args()

    logging.info(f"running in mode: {settings.mode}")
    if settings.mode == "one_shot":
        if settings.accounts is None:
            raise FinbotError("--accounts must be provided in on shot mode")
        run_one_shot(settings.accounts)
        return

    workers: list[Worker] = []

    logging.info("initializing scheduler thread")
    scheduler = Scheduler()
    workers.append(scheduler)

    StopHandler(workers)

    logging.info("starting all workers")
    for worker in workers:
        worker.start()

    logging.info("scheduler service is ready")
    for worker in workers:
        worker.join()


def main() -> int:
    try:
        main_impl()
        return 0
    except Exception:
        logging.error(f"fatal error while running schedsrv: \n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
