import asyncio

from finbot.apps.workersrv_temporal.worker import worker_main

if __name__ == "__main__":
    asyncio.run(worker_main())
