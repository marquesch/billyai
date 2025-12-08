from collections.abc import Generator

from sqlalchemy.exc import IntegrityError

from domain.entities import Category
from domain.exceptions import CategoryAlreadyExistsException
from domain.exceptions import CategoryNotFoundException
from infrastructure.persistence.database.models import DBCategory
from infrastructure.persistence.database.repositories import DBRepository


class DBCategoryRepository(DBRepository):
    def create(self, tenant_id: int, name: str, description: str) -> Category:
        db_category = DBCategory(tenant_id=tenant_id, name=name, description=description)

        self.session.add(db_category)

        try:
            self.session.flush()
        except IntegrityError:
            raise CategoryAlreadyExistsException

        self.session.refresh(db_category)

        return db_category.to_entity()

    def get_all(self, tenant_id: int) -> Generator[Category]:
        query = self.session.query(DBCategory).filter_by(tenant_id=tenant_id)
        return (db_category.to_entity() for db_category in query)

    def get_by_name(self, tenant_id: int, category_name: str) -> Category:
        db_category = self.session.query(DBCategory).filter_by(tenant_id=tenant_id, name=category_name).first()

        if db_category is None:
            raise CategoryNotFoundException

        return db_category.to_entity()

    def get_by_id(self, tenant_id: int, category_id: int) -> Category:
        db_category = self.session.query(DBCategory).filter_by(tenant_id=tenant_id, id=category_id).first()

        if db_category is None:
            raise CategoryNotFoundException

        return db_category.to_entity()

    def update(
        self,
        tenant_id: int,
        category_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> Category:
        db_category = self.session.query(DBCategory).filter_by(tenant_id=tenant_id, id=category_id).first()

        if db_category is None:
            raise CategoryNotFoundException

        if name is not None:
            db_category.name = name

        if description is not None:
            db_category.description = description

        try:
            self.session.flush()
        except IntegrityError as e:
            raise CategoryAlreadyExistsException from e

        return db_category.to_entity()
