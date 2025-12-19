import datetime

from domain.entities import Bill
from domain.ports.repositories import BillRepository
from domain.ports.repositories import CategoryRepository


class BillService:
    def __init__(self, bill_repository: BillRepository, category_repository: CategoryRepository):
        self._bill_repository: bill_repository
        self._category_repository: category_repository

    def create(self, tenant_id: int, date: datetime.date, value: float, category_id: int | None = None) -> Bill:
        if category_id is not None:
            self._category_repository.get_by_id(tenant_id=tenant_id, category_id=category_id)

        return self._bill_repository.create(tenant_id=tenant_id, date=date, value=value, category_id=category_id)

    def get_many(
        self,
        tenant_id: int,
        category_id: int | None = None,
        date_range: tuple[datetime.date, datetime.date] | None = None,
        value_range: tuple[float, float] | None = None,
    ) -> list[Bill]:
        return list(
            self._bill_repository.get_many(
                tenant_id=tenant_id,
                category_id=category_id,
                date_range=date_range,
                value_range=value_range,
            ),
        )

    def get_by_id(self, tenant_id: int, bill_id: int) -> Bill:
        return self._bill_repository.get_by_id(tenant_id=tenant_id, bill_id=bill_id)

    def update(
        self,
        tenant_id: int,
        bill_id: int,
        date: datetime.date | None = None,
        value: float | None = None,
        category_id: int | None = None,
    ) -> Bill:
        if category_id is not None:
            self._category_repository.get_by_id(tenant_id=tenant_id, category_id=category_id)

        return self._bill_repository.update(
            tenant_id=tenant_id, bill_id=bill_id, date=date, value=value, category_id=category_id
        )
