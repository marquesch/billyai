import datetime
from collections.abc import Generator

from domain.entities import Bill
from domain.exceptions import BillNotFoundException
from domain.exceptions import CategoryNotFoundException
from domain.exceptions import TenantNotFoundException
from infrastructure.persistence.memory.repositories import InMemoryRepository


class InMemoryBillRepository(InMemoryRepository):
    def create(self, tenant_id: int, date: datetime.date, value: float, category_id: int | None = None) -> Bill:
        if tenant_id not in self._in_memory_database.tenants:
            raise TenantNotFoundException

        category = self._in_memory_database.categories.get(category_id)
        if category is None or category.tenant_id != tenant_id:
            raise CategoryNotFoundException

        self._in_memory_database.bills_id_seq += 1
        bill = Bill(
            id=self._in_memory_database.bills_id_seq,
            value=value,
            date=date,
            category_id=category_id,
            tenant_id=tenant_id,
        )

        self._in_memory_database.bills[self._in_memory_database.bills_id_seq] = bill

        return bill

    def get_many(
        self,
        tenant_id: int,
        date_range: tuple[datetime.date, datetime.date] | None = None,
        category_id: int | None = None,
        value_range: tuple[float, float] | None = None,
    ) -> Generator[Bill]:
        def filter_bill(bill: Bill) -> bool:
            if bill.tenant_id != tenant_id:
                return False

            if date_range is not None and (bill.date < date_range[0] or bill.date > date_range[1]):
                return False

            if category_id is not None and bill.category_id != category_id:
                return False

            if value_range is not None and (bill.value < value_range[0] or bill.value > value_range[1]):
                return False

            return True

        return (bill for bill in filter(filter_bill, self._in_memory_database.bills.values()))

    def get_by_id(self, tenant_id: int, bill_id: int) -> Bill:
        bill = self._in_memory_database.bills.get(bill_id)

        return bill if bill and bill.tenant_id == tenant_id else None

    def update(
        self,
        tenant_id: int,
        bill_id: int,
        date: datetime.date | None = None,
        value: float | None = None,
        category_id: int | None = None,
    ) -> Bill:
        bill = self._in_memory_database.bills.get(bill_id)
        if bill is None or bill.tenant_id != tenant_id:
            raise BillNotFoundException

        if date is not None:
            bill.date = date

        if value is not None:
            bill.value = value

        if category_id is not None:
            category = self._in_memory_database.categories.get(category_id)
            if category is None or category.tenant_id != tenant_id:
                raise CategoryNotFoundException
            bill.category_id = category_id

        return bill
