import datetime
from collections.abc import Generator
from typing import Protocol
from typing import runtime_checkable

from domain.entities import Bill
from domain.entities import Category
from domain.entities import Tenant
from domain.entities import User


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


@runtime_checkable
class CategoryRepository(Protocol):
    def create(self, tenant_id: int, name: str, description: str) -> Category: ...
    def get_all(self, tenant_id: int) -> Generator[Category]: ...
    def get_by_name(self, tenant_id: int, category_name: str) -> Category: ...


@runtime_checkable
class TenantRepository(Protocol):
    def create(self) -> Tenant: ...


@runtime_checkable
class UserRepository(Protocol):
    def get_by_phone_number(self, phone_number: str) -> User | None: ...
    def get_by_id(self, user_id: int) -> User: ...
