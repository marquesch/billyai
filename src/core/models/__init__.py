import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm.query import Query


class Base(DeclarativeBase):
    pass


class TenantMixin:
    tenant_id = mapped_column(Integer, ForeignKey("tenant.id"), nullable=False)

    @declared_attr
    def tenant(cls):
        return relationship("Tenant")


class Tenant(Base):
    __tablename__ = "tenant"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    users = relationship("User", back_populates="tenant")
    bills = relationship("Bill", back_populates="tenant")
    categories = relationship("Category", back_populates="tenant")

    @classmethod
    def new(
        cls,
        session: Session,
        users: list["User"] = [],
        bills: list["Bill"] = [],
        categories: list["Category"] = [],
    ) -> "Tenant":
        tenant = cls(users=users, bills=bills, categories=categories)

        session.add(tenant)
        session.flush()
        session.refresh(tenant)

        return tenant


class User(Base, TenantMixin):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    phone_number = Column(String, nullable=False)
    name = Column(String, nullable=True)

    @classmethod
    def new(cls, session: Session, name: str, phone_number: str, tenant_id: int) -> "User":
        user = cls(name=name, phone_number=phone_number, tenant_id=tenant_id)

        session.add(user)
        session.flush()
        session.refresh(user)

        return user

    @classmethod
    def get_by_phone_number(cls, session: Session, phone_number: str) -> "User | None":
        return session.query(cls).filter_by(phone_number=phone_number).first()

    def to_dict(self):
        return {
            "phone_number": self.phone_number,
            "name": self.name,
        }


class Bill(Base, TenantMixin):
    __tablename__ = "bill"

    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)

    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    category = relationship("Category", back_populates="bills")

    @classmethod
    def register(
        cls,
        session: Session,
        tenant_id: int,
        date: datetime.datetime,
        value: float,
        category_id: int | None = None,
    ) -> "Bill":
        bill = cls(value=value, date=date, category_id=category_id, tenant_id=tenant_id)
        session.add(bill)
        session.commit()
        session.refresh(bill)

        return bill

    @classmethod
    def get_all(cls, session: Session, tenant_id: int) -> "list[Bill]":
        return session.query(cls).filter_by(tenant_id=tenant_id).all()

    @classmethod
    def get_many(
        cls,
        session: Session,
        tenant_id: int,
        date_range: tuple[datetime.datetime] | None = None,
        category_id: int | None = None,
        value_range: tuple[float] | None = None,
    ) -> "list[Bill]":
        print(date_range)
        print(category_id)
        print(value_range)

        query = session.query(cls).filter_by(tenant_id=tenant_id)

        if date_range is not None:
            query = query.filter(cls.date.between(*date_range))

        if category_id is not None:
            query = query.filter(cls.category_id == category_id)

        if value_range is not None:
            query = query.filter(cls.value.between(*value_range))

        return query.limit(10).all()

    @classmethod
    def get_by_id(cls, session: Session, tenant_id: int, bill_id: int) -> "Bill":
        return session.query(cls).filter_by(id=bill_id, tenant_id=tenant_id).first()

    def to_dict(self):
        return {
            "id": self.id,
            "value": self.value,
            "date": self.date.isoformat(),
            "category_id": self.category_id,
        }


class Category(Base, TenantMixin):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    bills = relationship("Bill", back_populates="category")

    @classmethod
    def create(cls, session: Session, tenant_id: int, name: str, description: str):
        category = cls(name=name, description=description, tenant_id=tenant_id)

        session.add(category)
        session.commit()
        session.refresh(category)

        return category

    @classmethod
    def get_all(cls, session: Session, tenant_id: int) -> Query:
        return session.query(cls).filter_by(tenant_id=tenant_id)

    @classmethod
    def get_by_id(cls, session: Session, tenant_id: int, category_id: int) -> "Category | None":
        return session.query(cls).filter_by(tenant_id=tenant_id).get(category_id)

    @classmethod
    def get_by_name(cls, session: Session, tenant_id: int, category_name: str) -> "Category | None":
        return session.query(cls).filter_by(tenant_id=tenant_id, name=category_name).first()

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}
