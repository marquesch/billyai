from collections.abc import Generator

from domain.entities import Category
from domain.exceptions import CategoryAlreadyExistsException
from domain.exceptions import CategoryNotFoundException
from infrastructure.persistence.memory.repositories import InMemoryRepository


class InMemoryCategoryRepository(InMemoryRepository):
    def _raise_if_name_already_exists_in_tenant(self, tenant_id: int, name: str) -> None:
        for category in self._in_memory_database.categories.values():
            if category.tenant_id == tenant_id and category.name == name:
                raise CategoryAlreadyExistsException

    def create(self, tenant_id: int, name: str, description: str) -> Category:
        self._raise_if_name_already_exists_in_tenant(tenant_id=tenant_id, name=name)

        self._in_memory_database.categories_id_seq += 1
        category = Category(self._in_memory_database.categories_id_seq, name, description, tenant_id)

        self._in_memory_database.categories[self._in_memory_database.categories_id_seq] = category

        return category

    def get_all(self, tenant_id: int) -> Generator[Category]:
        return (
            category
            for category in filter(
                lambda category: category.tenant_id == tenant_id,
                self._in_memory_database.categories.values(),
            )
        )

    def get_by_name(self, tenant_id: int, category_name: str) -> Category:
        categories = list(
            filter(
                lambda category: category.tenant_id == tenant_id and category.name == category_name,
                self._in_memory_database.categories.values(),
            ),
        )

        if categories and len(categories) == 1:
            return categories[0]

    def get_by_id(self, tenant_id: int, category_id: int) -> Category:
        category = self._in_memory_database.categories.get(category_id)

        return category if category and category.tenant_id == tenant_id else None

    def update(
        self,
        tenant_id: int,
        category_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> Category:
        category = self._in_memory_database.categories.get(category_id)

        if category is None or category.tenant_id != tenant_id:
            raise CategoryNotFoundException

        if name is not None:
            self._raise_if_name_already_exists_in_tenant(tenant_id=tenant_id, name=name)
            category.name = name

        if description is not None:
            category.description = description

        return category
