from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.config.settings import app_settings

engine = create_engine(app_settings.database_uri)
SessionLocal: type[sa.orm.Session] = sessionmaker(engine)


@contextmanager
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
