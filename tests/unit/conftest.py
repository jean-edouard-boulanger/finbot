from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finbot.core.environment import get_test_database_url
from finbot.model import Base as ModelBase
from finbot.model import SessionType


@pytest.fixture(scope="function")
def db_session() -> Generator[SessionType, None, None]:
    engine = create_engine(get_test_database_url())
    ModelBase.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    ModelBase.metadata.drop_all(engine)
