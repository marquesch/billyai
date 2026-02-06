import datetime
from collections.abc import Generator
from typing import Protocol

from domain.entities import Bill
from domain.entities import Category
from domain.entities import Message
from domain.entities import MessageAuthor
from domain.entities import MessageBroker
from domain.entities import Tenant
from domain.entities import User


class BillRepository(Protocol):
    def create(self, tenant_id: int, date: datetime.date, value: float, category_id: int | None = None) -> Bill: ...
    def get_many(
        self,
        tenant_id: int,
        category_id: int | None = None,
        date_range: tuple[datetime.date, datetime.date] | None = None,
        value_range: tuple[float, float] | None = None,
    ) -> Generator[Bill]: ...
    def get_by_id(self, tenant_id: int, bill_id: int) -> Bill: ...
    def update(
        self,
        tenant_id: int,
        bill_id: int,
        date: datetime.date | None = None,
        value: float | None = None,
        category_id: int | None = None,
    ) -> Bill: ...


class CategoryRepository(Protocol):
    def create(self, tenant_id: int, name: str, description: str) -> Category: ...
    def get_all(self, tenant_id: int) -> Generator[Category]: ...
    def get_by_name(self, tenant_id: int, category_name: str) -> Category: ...
    def get_by_id(self, tenant_id: int, category_id: int) -> Category: ...
    def update(self, tenant_id: int, category_id: int, name: str | None, description: str | None) -> Category: ...


class TenantRepository(Protocol):
    def create(self) -> Tenant: ...


class UserRepository(Protocol):
    def get_by_phone_number(self, phone_number: str) -> User | None: ...
    def get_by_id(self, user_id: int) -> User: ...
    def create(self, phone_number: str, name: str, is_registered: bool, tenant_id: int) -> User: ...
    def update(self, user_id: int, tenant_id: int, name: str, is_registered: bool) -> User: ...


class MessageRepository(Protocol):
    def create(
        self,
        body: str,
        author: MessageAuthor,
        timestamp: datetime.datetime,
        broker: MessageBroker,
        user_id: int,
        tenant_id: int,
        external_message_id: str | None = None,
    ) -> Message: ...
    def get_all(self, user_id: int, tenant_id: int) -> Generator[Message]: ...
    def get_by_id(self, message_id: int) -> Message: ...
