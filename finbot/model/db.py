from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from finbot.core import environment
from finbot.core.db.session import Session

db_engine = create_engine(environment.get_database_url())
db_session = Session(scoped_session(sessionmaker(bind=db_engine)))
