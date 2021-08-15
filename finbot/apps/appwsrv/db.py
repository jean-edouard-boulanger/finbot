from finbot.core import environment, dbutils

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import logging


logger = logging.getLogger(__name__)


logger.info("initializing database engine")
db_engine = create_engine(environment.get_database_url())

logger.info("initializing database session")
db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))
