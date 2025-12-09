import datetime

from domain.entities import Bill
from domain.entities import Category
from domain.entities import User
from domain.exceptions import UserNotFoundException
from domain.ports.repositories import BillRepository
from domain.ports.repositories import CategoryRepository
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository


class AIAgentService:
    def __init__(
        self,
        phone_number: str,
        user_repo: UserRepository,
        bill_repo: BillRepository,
        category_repo: CategoryRepository,
        tenant_repo: TenantRepository,
    ):
        self._phone_number = phone_number
        self._user_repo = user_repo
        self._bill_repo = bill_repo
        self._category_repo = category_repo
        self._tenant_repo = tenant_repo

        self._user = user_repo.get_by_phone_number(phone_number)

    def create_user(self, user_name: str) -> User:
        tenant = self._tenant_repo.create()
        default_category = self._category_repo.create(
            tenant.id, "default", "Default category, for everything that doesn't fit other categories"
        )
        user = self._user_repo.create(self._phone_number, user_name, tenant.id)

        self._user = user

        return user

    def create_category(self, name: str, description: str) -> Category:
        return self._category_repo.create(self._user.tenant_id, name, description)

    def get_all_categories(self) -> list[Category]:
        return list(self._category_repo.get_all(self._user.tenant_id))

    def create_bill(self, date: datetime.datetime, value: float, category_id: int) -> Bill:
        return self._bill_repo.create(self._user.tenant_id, date, value, category_id)

    def update_bill(
        self,
        bill_id: int,
        date: datetime.datetime | None,
        value: float | None,
        category_id: int | None,
    ) -> Bill:
        self._bill_repo.update(self._user.tenant_id, bill_id, date, value, category_id)

    def get_bills(
        self,
        category_id: int | None = None,
        date_range: tuple[datetime.datetime, datetime.datetime] | None = None,
        value_range: tuple[float, float] | None = None,
    ) -> list[Bill]:
        return list(self._bill_repo.get_many(self._user.tenant_id, category_id, date_range, value_range))
