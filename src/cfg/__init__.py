from typing import Type

import sqlalchemy as sa
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql+psycopg2://billy:billy@postgres:5432/billy?sslmode=disable", pool_size=60)
Session: type[sa.orm.Session] = sessionmaker(engine)


def db_session():
    try:
        session = Session()
        yield session
    except Exception:
        session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.close()
