from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from application.services.category_service import CategoryService
from domain.entities import User
from domain.exceptions import CategoryAlreadyExistsException
from domain.exceptions import CategoryNotFoundException
from presentation.api import dependencies

router = APIRouter(prefix="/categories")


class CategoryRequest(BaseModel):
    name: str
    description: str


@router.get("/")
def index(
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_service: Annotated[CategoryService, Depends(dependencies.get_category_service)],
):
    return [category for category in category_service.get_all(user.tenant_id)]


@router.get("/{category_id}")
def get_category(
    category_id: int,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_service: Annotated[CategoryService, Depends(dependencies.get_category_service)],
):
    try:
        return category_service.get_by_id(user.tenant_id, category_id)
    except CategoryNotFoundException as e:
        raise HTTPException(404, detail="Category not found") from e


@router.post("/", status_code=201)
def create_category(
    req: CategoryRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_service: Annotated[CategoryService, Depends(dependencies.get_category_service)],
):
    try:
        return category_service.create(user.tenant_id, req.name, req.description)
    except CategoryAlreadyExistsException as e:
        raise HTTPException(409, detail="Category already exists") from e


@router.put("/{category_id}")
def update_category(
    category_id: int,
    req: CategoryRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_service: Annotated[CategoryService, Depends(dependencies.get_category_service)],
):
    try:
        return category_service.update(user.tenant_id, category_id, req.name, req.description)
    except CategoryNotFoundException as e:
        raise HTTPException(404, detail="Category not found") from e
    except CategoryAlreadyExistsException as e:
        raise HTTPException(409, detail="Category already exists") from e
