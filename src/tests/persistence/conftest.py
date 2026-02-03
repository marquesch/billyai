import datetime

import pytest
from sqlalchemy import Engine
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from infrastructure.persistence.database.models import Base
from infrastructure.persistence.database.models import DBBill
from infrastructure.persistence.database.models import DBCategory
from infrastructure.persistence.database.models import DBTenant
from infrastructure.persistence.database.repositories.bill_repository import DBBillRepository


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Session:
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def db_bill_repository(session: Session) -> DBBillRepository:
    return DBBillRepository(session)


@pytest.fixture
def db_tenant(session: Session):
    """Create a test tenant."""
    db_tenant = DBTenant()
    session.add(db_tenant)
    session.flush()
    session.refresh(db_tenant)
    return db_tenant


@pytest.fixture
def db_category(session: Session, db_tenant: DBTenant) -> DBCategory:
    db_category = DBCategory(
        tenant_id=db_tenant.id,
        name="Groceries",
        description="Food and household items",
    )
    session.add(db_category)
    session.flush()
    session.refresh(db_category)
    return db_category


@pytest.fixture
def db_sample_bill(session: Session, db_tenant: DBTenant, db_category: DBCategory) -> DBBill:
    db_bill = DBBill(
        tenant_id=db_tenant.id,
        date=datetime.date(2025, 1, 15),
        value=150.50,
        category_id=db_category.id,
    )
    session.add(db_bill)
    session.flush()
    session.refresh(db_bill)
    return db_bill


@pytest.fixture
def another_db_tenant(session: Session) -> DBTenant:
    tenant = DBTenant()
    session.add(tenant)
    session.flush()
    session.refresh(tenant)

    return tenant


@pytest.fixture
def another_category(session: Session, db_tenant: DBTenant) -> DBCategory:
    other_category = DBCategory(
        tenant_id=db_tenant.id,
        name="Transport",
        description="Transportation costs",
    )
    session.add(other_category)
    session.flush()
    session.refresh(other_category)

    return other_category


@pytest.fixture
def another_bill(session: Session, db_tenant: DBTenant, another_category: DBCategory) -> DBBill:
    new_bill = DBBill(
        tenant_id=db_tenant.id,
        date=datetime.date(2025, 1, 25),
        value=50.00,
        category_id=another_category.id,
    )
    session.add(new_bill)
    session.flush()
    session.refresh(new_bill)

    return new_bill


@pytest.fixture
def db_bills(session: Session, db_tenant: DBTenant, db_category: DBCategory):
    bills = [
        DBBill(
            tenant_id=db_tenant.id,
            date=datetime.date(2025, 1, 10),
            value=100.00,
            category_id=db_category.id,
        ),
        DBBill(
            tenant_id=db_tenant.id,
            date=datetime.date(2025, 1, 15),
            value=200.00,
            category_id=db_category.id,
        ),
        DBBill(
            tenant_id=db_tenant.id,
            date=datetime.date(2025, 1, 20),
            value=300.00,
            category_id=db_category.id,
        ),
        DBBill(
            tenant_id=db_tenant.id,
            date=datetime.date(2025, 2, 5),
            value=150.00,
            category_id=db_category.id,
        ),
    ]
    session.add_all(bills)
    session.flush()
    return bills
