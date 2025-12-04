import datetime
from collections.abc import Generator
from typing import Protocol
from typing import runtime_checkable

from domain.entities import Bill


@runtime_checkable
class BillRepository(Protocol):
    def create(self, tenant_id: int, date: datetime.datetime, value: float, category_id: int | None = None) -> Bill: ...
    def get_many(
        self,
        tenant_id: int,
        date_range: tuple[datetime.datetime] | None = None,
        category_id: int | None = None,
        value_range: tuple[float] | None = None,
    ) -> Generator[Bill]: ...
    def get_by_id(self, tenant_id: int, bill_id: int) -> Bill: ...
