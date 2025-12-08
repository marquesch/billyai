from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from api import dependencies
from domain.entities import User
from domain.exceptions import CategoryAlreadyExistsException
from domain.exceptions import CategoryNotFoundException
from domain.ports.repositories import CategoryRepository

router = APIRouter(prefix="/categories")


class CategoryRequest(BaseModel):
    name: str
    description: str


@router.get("/")
def index(
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_repository: Annotated[CategoryRepository, Depends(dependencies.get_category_repository)],
):
    return [category for category in category_repository.get_all(user.tenant_id)]


@router.get("/{category_id}")
def get_category(
    category_id: int,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_repository: Annotated[CategoryRepository, Depends(dependencies.get_category_repository)],
):
    try:
        return category_repository.get_by_id(user.tenant_id, category_id)
    except CategoryNotFoundException as e:
        raise HTTPException(404, detail="Category not found") from e


@router.post("/", status_code=201)
def create_category(
    req: CategoryRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_repository: Annotated[CategoryRepository, Depends(dependencies.get_category_repository)],
):
    try:
        return category_repository.create(user.tenant_id, req.name, req.description)
    except CategoryAlreadyExistsException as e:
        raise HTTPException(409, detail="Category already exists") from e


@router.put("/{category_id}")
def update_category(
    category_id: int,
    req: CategoryRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_repository: Annotated[CategoryRepository, Depends(dependencies.get_category_repository)],
):
    try:
        return category_repository.update(user.tenant_id, category_id, req.name, req.description)
    except CategoryNotFoundException as e:
        raise HTTPException(404, detail="Category not found") from e
    except CategoryAlreadyExistsException as e:
        raise HTTPException(409, detail="Category already exists") from e
