from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse

from core.models import User
from libs import auth as auth_lib
from service.category import CategoryService
from service.category import get_category_svc

category_router = APIRouter(prefix="/categories")


@category_router.get("/")
def index(
    per_page: int,
    page: int,
    user: Annotated[User, Depends(auth_lib.authenticated_user)],
    category_service: Annotated[CategoryService, Depends(get_category_svc)],
):
    categories = [category.to_dict() for category in category_service.get_categories(user, per_page, page)]

    return JSONResponse({"data": categories})
