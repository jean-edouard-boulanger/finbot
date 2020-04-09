from finbot.clients.snap import SnapClient
from finbot.clients.history import HistoryClient
from finbot.core import dbutils, utils
from finbot.model import UserAccount
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
import time
import stackprinter
import logging.config
import logging
import os


logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s (%(threadName)s) [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


def run_workflow(user_account_id, snap_client, hist_client):
    logging.info(f"starting workflow for user_id={user_account_id}")

    logging.info(f"will take raw snapshot")

    snapshot_metadata = snap_client.take_snapshot(user_account_id)
    logging.debug(snapshot_metadata)

    snapshot_id = snapshot_metadata["snapshot"]["identifier"]
    
    logging.info(f"raw snapshot created with id={snapshot_id}")
    logging.debug(snapshot_metadata)

    logging.info(f"will write history report")
    
    history_metadata = hist_client.write_history(snapshot_id)
    
    history_entry_id = history_metadata["report"]["history_entry_id"]
    logging.info(f"history report written with id={history_entry_id}")
    logging.debug(utils.pretty_dump(history_metadata))

    logging.info(f"workflow done for user_id={user_account_id}")


def create_parser():
    parser = argparse.ArgumentParser(description="valuation and reporting scheduler")
    parser.add_argument("--mode", choices={"server", "one_shot"}, type=str, default="server")
    parser.add_argument("--accounts", type=lambda v: set(int(i) for i in v.split(",")), default=None)
    return parser


def main():
    settings = create_parser().parse_args()
    logging.info(f"running in mode: {settings.mode}")

    db_engine = create_engine(os.environ['FINBOT_DB_URL'])
    db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))

    snapwsrv_endpoint = os.environ["FINBOT_SNAPWSRV_ENDPOINT"]
    snap_client = SnapClient(snapwsrv_endpoint)
    logging.info(f"snapshot client created with {snapwsrv_endpoint} endpoint")

    histwsrv_endpoint = os.environ["FINBOT_HISTWSRV_ENDPOINT"]
    hist_client = HistoryClient(histwsrv_endpoint)
    logging.info(f"history report client created with {histwsrv_endpoint} endpoint")

    while True:
        for user_account in db_session.query(UserAccount).all():
            if not settings.accounts or user_account.id in settings.accounts:
                try:
                    run_workflow(
                        user_account_id=user_account.id,
                        snap_client=snap_client,
                        hist_client=hist_client)
                except Exception as e:
                    logging.warning(f"failure while running workflow for "
                                    f"user_id={user_account.id}: {e}, "
                                    f"trace: \n{stackprinter.format()}")
        if settings.mode == "one_shot":
            break

        time.sleep(24 * 3600)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"fatal error while running schedsrv: \n{stackprinter.format()}")
