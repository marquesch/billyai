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


class CategoryService(Service):
    def get_categories(self, user: User, per_page: int, page: int):
        categories_query = paginate(Category.get_all(self.session, user.tenant_id), per_page=per_page, page=page)

        yield from (category for category in categories_query)

    def new_category(self, user: User, name: str, description: str) -> Category: ...


def get_category_svc(
    cache: Annotated[Cache, Depends(get_cache)],
    session: Annotated[Session, Depends(db_session)],
):
    return CategoryService(session, cache)
