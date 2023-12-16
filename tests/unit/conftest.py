from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finbot.core.db.session import Session as DBSession
from finbot.model import Base as ModelBase


@pytest.fixture(scope="function")
def db_session() -> Generator[DBSession, None, None]:
    engine = create_engine("sqlite://")
    ModelBase.metadata.create_all(engine)
    session = DBSession(sessionmaker(bind=engine)())
    yield session
    ModelBase.metadata.drop_all(engine)
