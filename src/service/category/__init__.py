from collections.abc import Generator
from typing import Annotated

from fastapi import Depends

from cfg import Session
from cfg import db_session
from core.models import Category
from core.models import User
from libs.cache import Cache
from libs.cache import get_cache
from libs.pagination import paginate
from service import Service


class CategoryNotFoundException(Exception):
    pass


class CategoryExistsException(Exception):
    pass


class CategoryService(Service):
    def get_categories(self, tenant_id: int, per_page: int, page: int) -> Generator[Category]:
        categories_query = paginate(Category.get_all(self.session, tenant_id), per_page=per_page, page=page)

        yield from (category for category in categories_query)

    def get_category(self, tenant_id: int, category_id: int) -> Category:
        category = Category.get_by_id(self.session, tenant_id, category_id)

        if category is None:
            raise CategoryNotFoundException

        return category

    def create_category(self, tenant_id: int, name: str, description: str) -> Category:
        category = Category.get_by_name(self.session, tenant_id, name)
        if category is not None:
            raise CategoryExistsException

        return Category.create(self.session, tenant_id, name, description)

    def update_category(self, tenant_id: int, category_id: int, name: str, description: str) -> Category:
        category = Category.get_by_id(self.session, tenant_id, category_id)

        if category is None:
            raise CategoryNotFoundException

        category.name = name
        category.description = description

        return category


def get_category_svc(
    cache: Annotated[Cache, Depends(get_cache)],
    session: Annotated[Session, Depends(db_session)],
):
    return CategoryService(session, cache)
