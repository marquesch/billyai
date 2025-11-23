from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
from typing import Type

engine = create_engine("postgresql+psycopg2://billy:billy@localhost:5432/billy?sslmode=disable")
Session: Type[sa.orm.Session] = sessionmaker(engine)
