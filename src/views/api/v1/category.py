from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.models import User
from libs import auth as auth_lib
from service.category import CategoryExistsException
from service.category import CategoryNotFoundException
from service.category import CategoryService
from service.category import get_category_svc

category_router = APIRouter(prefix="/categories")


class CategoryRequest(BaseModel):
    name: str
    description: str


@category_router.get("/")
def index(
    per_page: int,
    page: int,
    user: Annotated[User, Depends(auth_lib.authenticated_user)],
    category_service: Annotated[CategoryService, Depends(get_category_svc)],
):
    categories = [category.to_dict() for category in category_service.get_categories(user, per_page, page)]

    return JSONResponse({"data": categories}, 200)


@category_router.post("/")
def create_category(
    req: CategoryRequest,
    user: Annotated[User, Depends(auth_lib.authenticated_user)],
    category_service: Annotated[CategoryService, Depends(get_category_svc)],
):
    try:
        category = category_service.new_category(user, req.name, req.description)
    except CategoryExistsException as e:
        raise HTTPException(409, detail="Category with this name already exists") from e

    return JSONResponse({"data": category.to_dict()}, 201)


@category_router.put("/{category_id}")
def update_category(
    category_id: int,
    req: CategoryRequest,
    user: Annotated[User, Depends(auth_lib.authenticated_user)],
    category_service: Annotated[CategoryService, Depends(get_category_svc)],
):
    try:
        category = category_service.update_category(user, category_id, req.name, req.description)
    except CategoryNotFoundException as e:
        raise HTTPException(404, detail="Category not found") from e

    return JSONResponse({"data": category.to_dict()}, 200)
