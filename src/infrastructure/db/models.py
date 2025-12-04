from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from domain.entities import Bill
from domain.entities import Category
from domain.entities import Tenant
from domain.entities import User

Base = declarative_base()


class TenantMixin:
    tenant_id = mapped_column(Integer, ForeignKey("tenant.id"), nullable=False)

    @declared_attr
    def tenant(cls):
        return relationship("Tenant")


class DBTenant(Base):
    __tablename__ = "tenant"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    users = relationship("User", back_populates="tenant")
    bills = relationship("Bill", back_populates="tenant")
    categories = relationship("Category", back_populates="tenant")

    def __init__(self, tenant: Tenant):
        self.id = tenant.id

    def to_entity(self):
        return Tenant(id=self.id)


class DBUser(Base, TenantMixin):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    phone_number = Column(String, nullable=False)
    name = Column(String, nullable=True)

    def to_entity(self):
        return User(id=self.id, phone_number=self.phone_number, name=self.name)


class DBBill(Base, TenantMixin):
    __tablename__ = "bill"

    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)

    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    category = relationship("Category", back_populates="bills")

    def to_entity(self):
        return Bill(id=self.id, value=self.value, date=self.date, category_id=self.category_id)


class DBCategory(Base, TenantMixin):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    bills = relationship("Bill", back_populates="category")

    def to_entity(self):
        return Category(id=self.id, name=self.name, description=self.description)
