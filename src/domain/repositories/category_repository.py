from typing import Protocol, runtime_checkable

from domain.entities import Category
from typing import Generator


@runtime_checkable
class CategoryRepository(Protocol):
    def create(self, tenant_id: int, name: str, description: str) -> Category: ...
    def get_all(self, tenant_id: int) -> Generator[Category]: ...
    def get_by_name(self, tenant_id: int, category_name: str) -> Category: ...
