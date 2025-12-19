from collections.abc import Generator

from domain.entities import Category
from domain.ports.repositories import CategoryRepository


class CategoryService:
    # TODO: create methods (simlpy call repository for now)
    def __init__(self, category_repository: CategoryRepository):
        self._category_repository = category_repository

    def create(self, tenant_id: int, name: str, description: str) -> Category:
        return self._category_repository.create(tenant_id=tenant_id, name=name, description=description)

    def get_all(self, tenant_id: int) -> Generator[Category]:
        return self._category_repository.get_all(tenant_id=tenant_id)

    def get_by_name(self, tenant_id: int, category_name: str) -> Category:
        return self._category_repository.get_by_name(tenant_id=tenant_id, category_name=category_name)

    def get_by_id(self, tenant_id: int, category_id: int) -> Category:
        return self._category_repository.get_by_id(tenant_id=tenant_id, category_id=category_id)

    def update(self, tenant_id: int, category_id: int, name: str | None, description: str | None) -> Category:
        return self._category_repository.update(
            tenant_id=tenant_id, category_id=category_id, name=name, description=description
        )
