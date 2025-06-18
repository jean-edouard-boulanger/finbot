#!/usr/bin/env python3
import asyncio
import enum
import json
import logging
import logging.config
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Coroutine, Protocol, cast

import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from finbot.apps.workersrv_temporal.worker import HealthcheckWorkflow
from finbot.core import environment
from finbot.core.async_ import maybe_awaitable
from finbot.core.logging import configure_logging
from finbot.core.temporal_ import GENERIC_TASK_QUEUE, get_temporal_client, temporal_workflow_id
from finbot.core.utils import float_or_none

configure_logging()


DEFAULT_TIMEOUT = timedelta(seconds=120)
WEB_SERVICES = ("appwsrv",)


class ExitCode(enum.Enum):
    Ok = 0
    Timeout = 1
    Error = 2


class Error(RuntimeError):
    pass


class Checker(Protocol):
    def __call__(self) -> bool | Coroutine[Any, Any, bool]:
        pass


class TemporalServerChecker(Checker):
    async def __call__(self) -> bool:
        try:
            await get_temporal_client()
            return True
        except Exception:
            return False


class TemporalWorkerChecker(Checker):
    async def __call__(self) -> bool:
        try:
            client = await get_temporal_client()
            return await client.execute_workflow(
                HealthcheckWorkflow.run,
                id=temporal_workflow_id(prefix="wait_deps/"),
                task_queue=GENERIC_TASK_QUEUE,
                execution_timeout=timedelta(seconds=1.0),
            )
        except Exception:
            return False


class ClientChecker(Checker):
    def __init__(self, endpoint: str):
        self._endpoint = endpoint

    def __call__(self) -> bool:
        try:
            response = requests.get(f"{self._endpoint}/healthy")
            if not response:
                return False
            return cast(bool, json.loads(response.content)["healthy"])
        except requests.RequestException:
            return False


class WebsiteChecker(Checker):
    def __init__(self, url: str):
        self._url = url

    def __call__(self) -> bool:
        try:
            requests.get(f"{self._url}")
            return True
        except requests.RequestException:
            return False


class DbChecker(Checker):
    def __init__(self, db_url: str):
        engine = create_engine(db_url)
        self._session = sessionmaker(bind=engine)()

    def __call__(self) -> bool:
        try:
            self._session.execute(text("SELECT 1"))
            return True
        except OperationalError:
            return False


def get_checker(dep_name: str) -> Checker:
    if dep_name == "finbotdb":
        database_url = environment.get_database_url()
        logging.info(f"will wait on '{dep_name}': {database_url}")
        return DbChecker(database_url)
    if dep_name == "finbotdb-test":
        test_database_url = environment.get_test_database_url()
        logging.info(f"will wait on '{dep_name}': {test_database_url}")
        return DbChecker(test_database_url)
    if dep_name == "temporal":
        logging.info(f"will wait on '{dep_name}'")
        return TemporalServerChecker()
    if dep_name == "workersrv[temporal]":
        logging.info(f"will wait on '{dep_name}'")
        return TemporalWorkerChecker()
    if dep_name in WEB_SERVICES:
        endpoint = environment.get_web_service_endpoint(dep_name)
        logging.info(f"will wait on '{dep_name}': {endpoint}")
        return ClientChecker(endpoint)
    if dep_name == "webapp":
        webapp_endpoint = environment.get_webapp_endpoint()
        logging.info(f"will wait on 'webapp': {webapp_endpoint}")
        return WebsiteChecker(webapp_endpoint)
    raise Error(f"Unknown dependency: {dep_name}")


async def main_impl() -> ExitCode:
    raw_deps = os.environ.get("FINBOT_WAIT_DEPS", sys.argv[1] if len(sys.argv) > 1 else None)
    raw_timeout = os.environ.get("FINBOT_WAIT_TIMEOUT")
    if raw_timeout is None:
        timeout = DEFAULT_TIMEOUT
        logging.warning(f"no timeout specified, defaulting to {timeout.total_seconds()}s")
    else:
        timeout_seconds = float_or_none(raw_timeout)
        if not timeout_seconds:
            timeout = DEFAULT_TIMEOUT
            logging.warning(f"invalid timeout specified ({raw_timeout}), defaulting to {timeout.total_seconds()}s")
        else:
            timeout = timedelta(seconds=timeout_seconds)
    start_time = datetime.now()
    if str(raw_deps).lower() in {"none", "0", "disabled"}:
        logging.warning(f"No dependencies to wait on (FINBOT_WAIT_DEPS={raw_deps})")
        return ExitCode.Ok
    assert isinstance(raw_deps, str)
    deps = list(set(raw_deps.split(",")))
    resolved = set()
    checkers = {dep: get_checker(dep) for dep in deps}
    wait_interval = int(os.environ.get("FINBOT_WAIT_INTERVAL", 3))
    logging.info(f"waiting on the following dependencies: {', '.join(checkers.keys())}")
    while True:
        for dep, checker in checkers.items():
            if dep not in resolved:
                try:
                    if await maybe_awaitable(checker()):
                        resolved.add(dep)
                        logging.info(f"🟢dependency {dep} is now available")
                    else:
                        logging.info(f"🟡dependency {dep} is not yet available")
                except Exception as e:
                    logging.error(f"fatal error while checking dependency {dep}: {e}")
                    raise
        if len(resolved) == len(checkers):
            break
        if timeout and datetime.now() - start_time > timeout:
            logging.warning(f"still waiting for dependencies after timeout ({timeout.total_seconds()}s), aborting")
            return ExitCode.Timeout
        time.sleep(wait_interval)
    logging.info(f"✅ all dependencies available: {', '.join(deps)}")
    return ExitCode.Ok


async def main() -> ExitCode:
    try:
        return await main_impl()
    except Exception as e:
        logging.error(f"leaving early because of uncaught error: {e}")
        return ExitCode.Error


if __name__ == "__main__":
    asyncio.run(main())
