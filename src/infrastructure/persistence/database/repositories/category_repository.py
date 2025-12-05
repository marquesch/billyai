from collections.abc import Generator

from domain.entities import Category
from domain.exceptions import ResourceNotFoundException
from infrastructure.persistence.database.models import DBCategory
from infrastructure.persistence.database.repositories import DBRepository


class DBCategoryRepository(DBRepository):
    def create(self, tenant_id: int, name: str, description: str) -> Category:
        db_category = DBCategory(tenant_id=tenant_id, name=name, description=description)

        self.session.add(db_category)
        self.session.flush(db_category)
        self.session.refresh(db_category)

        return db_category.to_entity()

    def get_all(self, tenant_id: int) -> Generator[Category]:
        query = self.session.query(DBCategory).filter_by(tenant_id=tenant_id)
        return (db_category.to_entity() for db_category in query)

    def get_by_name(self, tenant_id: int, category_name: str) -> Category:
        db_category = self.session.query(DBCategory).filter_by(tenant_id=tenant_id, name=category_name).first()

        if db_category is None:
            raise ResourceNotFoundException

        return db_category.to_entity()
