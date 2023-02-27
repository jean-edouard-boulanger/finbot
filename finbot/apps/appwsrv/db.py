import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from finbot.core import environment
from finbot.core.db.session import Session

logger = logging.getLogger(__name__)


logger.info("initializing database engine")
db_engine = create_engine(environment.get_database_url())

logger.info("initializing database session")
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))
