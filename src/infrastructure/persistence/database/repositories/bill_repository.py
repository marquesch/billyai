import datetime
from collections.abc import Generator

from domain.entities import Bill
from domain.exceptions import ResourceNotFoundException
from infrastructure.persistence.database.models import DBBill
from infrastructure.persistence.database.repositories import DBRepository


class DBBillRepository(DBRepository):
    def create(self, tenant_id: int, date: datetime.datetime, value: float, category_id: int | None = None) -> Bill:
        db_bill = DBBill(tenant_id=tenant_id, date=date, value=value, category_id=category_id)

        self.session.add(db_bill)
        self.session.flush()
        self.session.refresh(db_bill)

        return db_bill.to_entity()

    def get_many(
        self,
        tenant_id: int,
        date_range: tuple[datetime.datetime] | None = None,
        category_id: int | None = None,
        value_range: tuple[float] | None = None,
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
            raise ResourceNotFoundException

        return db_bill.to_entity()
