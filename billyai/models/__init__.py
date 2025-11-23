import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    phone_number = Column(String, nullable=False)
    name = Column(String, nullable=True)

    bills = relationship("Bill", back_populates="user")
    categories = relationship("Category", back_populates="user")

    @classmethod
    def get_by_phone_number(cls, session: Session, phone_number: str) -> "User | None":
        return session.query(cls).filter_by(phone_number=phone_number).first()


class Bill(Base):
    __tablename__ = "bill"

    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="bills")

    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    category = relationship("Category", back_populates="bills")

    @classmethod
    def register(
        cls,
        session: Session,
        user_id: int,
        date: datetime.datetime,
        value: float,
        category_id: int | None = None,
    ) -> "Bill":
        bill = cls(value=value, date=date, category_id=category_id)
        session.add(bill)
        session.commit()
        session.refresh(bill)

        return bill

    @classmethod
    def get_all(cls, session: Session) -> "list[Bill]":
        return session.query(cls).all()


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="categories")

    bills = relationship("Bill", back_populates="category")
