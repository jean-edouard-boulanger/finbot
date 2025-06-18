import abc
import argparse
import asyncio
import logging
import signal
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from types import FrameType
from typing import Generator

import schedule

from finbot.core import environment
from finbot.core.jobs import JobPriority, JobSource
from finbot.core.logging import configure_logging
from finbot.model import UserAccount, db, with_scoped_session
from finbot.workflows.user_account_valuation import client as valuation_client
from finbot.workflows.user_account_valuation.schema import ValuationRequest

configure_logging(environment.get_desired_log_level())


@dataclass(frozen=True)
class ValuationScheduleEntry:
    time_str: str
    tz: str = "Europe/Paris"
    notify_valuation: bool = False


VALUATION_SCHEDULE = [
    ValuationScheduleEntry("08:00"),
    ValuationScheduleEntry("10:00"),
    ValuationScheduleEntry("12:00"),
    ValuationScheduleEntry("14:00"),
    ValuationScheduleEntry("16:00"),
    ValuationScheduleEntry("18:00", notify_valuation=True),
]


class Worker(abc.ABC, threading.Thread):
    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def stop(self) -> None:
        pass


def parse_valuation_requests(
    raw_accounts_str: str,
) -> list[ValuationRequest]:
    requests = []
    raw_accounts = raw_accounts_str.split(";")
    for raw_account in raw_accounts:
        if ":" in raw_account:
            account_id_str, linked_accounts_str = raw_account.split(":")
            request = ValuationRequest(
                user_account_id=int(account_id_str),
                linked_accounts=[
                    int(linked_account_id_str) for linked_account_id_str in linked_accounts_str.split(",")
                ],
            )
        else:
            request = ValuationRequest(user_account_id=int(raw_account))
        requests.append(request)
    return requests


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="valuation and reporting scheduler",
    )
    parser.add_argument(
        "--mode",
        choices={"server", "one_shot"},
        type=str,
        default="server",
    )
    parser.add_argument(
        "--accounts",
        type=parse_valuation_requests,
        default=None,
    )
    return parser


def iter_user_accounts() -> Generator[UserAccount, None, None]:
    for user_account in db.session.query(UserAccount).all():
        yield user_account


class Scheduler(Worker):
    def __init__(self) -> None:
        super().__init__()
        self._scheduler = schedule.Scheduler()
        self._stop_event = threading.Event()
        self._loop = asyncio.new_event_loop()
        for schedule_entry in VALUATION_SCHEDULE:
            self._scheduler.every().day.at(schedule_entry.time_str, tz=schedule_entry.tz).do(
                with_scoped_session(self._dispatch_valuation),
                notify_valuation=schedule_entry.notify_valuation,
            )

    def _dispatch_valuation(self, notify_valuation: bool = False) -> None:
        logging.info("[scheduler thread] dispatching valuation for all accounts")
        user_account: UserAccount
        for user_account in iter_user_accounts():
            user_account_id = user_account.id
            if not user_account.settings.schedule_valuation:
                continue
            logging.info(f"[scheduler thread] dispatching valuation for user_account_id={user_account_id}")
            self._loop.run_until_complete(
                valuation_client.kickoff_valuation(
                    request=ValuationRequest(
                        user_account_id=user_account_id,
                        notify_valuation=notify_valuation,
                    ),
                    priority=JobPriority.medium,
                    job_source=JobSource.schedule,
                )
            )

    def run(self) -> None:
        logging.info("[scheduler thread] starting")
        if not environment.is_production():
            logging.warning(
                f"[scheduler thread] not scheduling jobs in the '{environment.get_finbot_runtime()}' environment"
            )
            while not self._stop_event.is_set():
                time.sleep(1.0)
        else:
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
    create_parser().parse_args()
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
