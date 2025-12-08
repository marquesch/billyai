import datetime

from domain.entities import Bill
from domain.entities import Category
from domain.entities import User
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
        self.phone_number = phone_number
        self.user_repo = user_repo
        self.bill_repo = bill_repo
        self.category_repo = category_repo
        self.tenant_repo = tenant_repo

        self.user = user_repo.get_by_phone_number(phone_number)

    def create_user(self, user_name: str) -> User:
        tenant = self.tenant_repo.create()
        user = self.user_repo.create(self.phone_number, user_name, tenant.id)

        self.user = user

        return user

    def get_user_name(self) -> str | None:
        return self.user and self.user.name

    def create_category(self, name: str, description: str) -> Category:
        return self.category_repo.create(self.user.tenant_id, name, description)

    def get_all_categories(self) -> list[Category]:
        return list(self.category_repo.get_all(self.user.tenant_id))

    def create_bill(self, date: datetime.datetime, value: float, category_id: int) -> Bill:
        return self.bill_repo.create(self.user.tenant_id, date, value, category_id)
