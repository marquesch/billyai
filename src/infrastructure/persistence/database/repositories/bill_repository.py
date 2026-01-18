import datetime
from collections.abc import Generator

from domain.entities import Bill
from domain.exceptions import BillNotFoundException
from infrastructure.persistence.database.models import DBBill
from infrastructure.persistence.database.repositories import DBRepository
from infrastructure.persistence.database.repositories import InMemoryRepository


class DBBillRepository(DBRepository):
    def _get_bill_or_raise(self, tenant_id: int, bill_id: int) -> DBBill:
        db_bill = self.session.query(DBBill).filter_by(tenant_id=tenant_id, id=bill_id).first()

        if db_bill is None:
            raise BillNotFoundException

        return db_bill

    def create(self, tenant_id: int, date: datetime.date, value: float, category_id: int | None = None) -> Bill:
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


class InMemoryBillRepository(InMemoryRepository):
    def create(self, tenant_id: int, date: datetime.date, value: float, category_id: int | None = None) -> Bill:
        if tenant_id not in self._tenants:
            raise ValueError("tenant not found")

        if category_id not in self._categories:
            raise ValueError("category not found")

        self._bills_id_seq += 1
        bill = Bill(id=self._bills_id_seq, value=value, date=date, category_id=category_id, tenant_id=tenant_id)

        self._bills[self._bills_id_seq] = bill

        return bill

    def get_many(
        self,
        tenant_id: int,
        date_range: tuple[datetime.date, datetime.date] | None = None,
        category_id: int | None = None,
        value_range: tuple[float, float] | None = None,
    ) -> Generator[Bill]:
        def filter_bill(bill: Bill):
            if bill.tenant_id != tenant_id:
                return False

            if date_range is not None and not date_range[0] <= bill.date <= date_range[1]:
                return False

            if category_id is not None and bill.category_id != category_id:
                return False

            if value_range is not None and not value_range[0] <= bill.value <= value_range[1]:
                return False

            return True

        return (bill for bill in filter(filter_bill, self._bills.values()))

    def get_by_id(self, tenant_id: int, bill_id: int) -> Bill:
        bill = self._bills.get(bill_id)

        return bill if bill.tenant_id == tenant_id else None

    def update(
        self,
        tenant_id: int,
        bill_id: int,
        date: datetime.date | None = None,
        value: float | None = None,
        category_id: int | None = None,
    ) -> Bill:
        bill = self._bills.get(bill_id)
        if bill is None:
            raise BillNotFoundException

        if date is not None:
            bill.date = date

        if value is not None:
            bill.value = value

        if value is not None:
            bill.value = value

        if category_id is not None:
            bill.category_id

        return bill
