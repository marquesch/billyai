import datetime
from collections.abc import Generator

from domain.entities import Bill
from domain.exceptions import BillNotFoundException
from domain.exceptions import CategoryNotFoundException
from domain.exceptions import TenantNotFoundException
from infrastructure.persistence.database.models import DBBill
from infrastructure.persistence.database.models import DBCategory
from infrastructure.persistence.database.models import DBTenant
from infrastructure.persistence.database.repositories import DBRepository


class DBBillRepository(DBRepository):
    def _get_bill_or_raise(self, tenant_id: int, bill_id: int) -> DBBill:
        db_bill = self.session.query(DBBill).filter_by(tenant_id=tenant_id, id=bill_id).first()

        if db_bill is None:
            raise BillNotFoundException

        return db_bill

    def create(self, tenant_id: int, date: datetime.date, value: float, category_id: int) -> Bill:
        db_tenant = self.session.query(DBTenant).get(tenant_id)

        if db_tenant is None:
            raise TenantNotFoundException

        db_category = self.session.query(DBCategory).filter_by(id=category_id, tenant_id=tenant_id).first()

        if db_category is None:
            raise CategoryNotFoundException

        db_bill = DBBill(tenant_id=tenant_id, date=date, value=value, category_id=category_id)

        self.session.add(db_bill)
        self.session.flush()
        self.session.refresh(db_bill)

        return db_bill.to_entity()

    def get_many(
        self,
        tenant_id: int,
        date_range: tuple[datetime.date, datetime.date] | None = None,
        category_id: int | None = None,
        value_range: tuple[float, float] | None = None,
    ) -> Generator[Bill]:
        query = self.session.query(DBBill).filter_by(tenant_id=tenant_id)

        if date_range is not None:
            query = query.filter(DBBill.date.between(*date_range))

        if category_id is not None:
            query = query.filter_by(category_id=category_id)

        if value_range:
            query = query.filter(DBBill.value.between(*value_range))

        return (db_bill.to_entity() for db_bill in query)

    def get_by_id(self, tenant_id: int, bill_id: int) -> Bill:
        db_bill = self.session.query(DBBill).filter_by(tenant_id=tenant_id, id=bill_id).first()

        if db_bill is None:
            raise BillNotFoundException

        return db_bill.to_entity()

    def update(
        self,
        tenant_id: int,
        bill_id: int,
        date: datetime.date | None = None,
        value: float | None = None,
        category_id: int | None = None,
    ) -> Bill:
        db_bill = self._get_bill_or_raise(tenant_id, bill_id)

        if date is not None:
            db_bill.date = date

        if value is not None:
            db_bill.value = value

        if category_id is not None:
            db_bill.category_id = category_id

        return db_bill.to_entity()
