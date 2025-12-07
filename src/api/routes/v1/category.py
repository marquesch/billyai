from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api import dependencies
from domain.entities import User
from domain.exceptions import CategoryAlreadyExists
from domain.exceptions import ResourceNotFoundException
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
    categories = [asdict(category) for category in category_repository.get_all(user.tenant_id)]

    return JSONResponse({"data": categories}, 200)


@router.get("/{category_id}")
def get_category(
    category_id: int,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_repository: Annotated[CategoryRepository, Depends(dependencies.get_category_repository)],
):
    try:
        category = category_repository.get_by_id(user.tenant_id, category_id)
    except ResourceNotFoundException as e:
        raise HTTPException(404, detail="Category not found") from e

    return JSONResponse({"data": asdict(category)})


@router.post("/")
def create_category(
    req: CategoryRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_repository: Annotated[CategoryRepository, Depends(dependencies.get_category_repository)],
):
    try:
        category = category_repository.create(user.tenant_id, req.name, req.description)
    except CategoryAlreadyExists as e:
        raise HTTPException(409, detail="Category already exists") from e

    return JSONResponse({"data": asdict(category)}, 201)


@router.put("/{category_id}")
def update_category(
    category_id: int,
    req: CategoryRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    category_repository: Annotated[CategoryRepository, Depends(dependencies.get_category_repository)],
):
    try:
        category = category_repository.update(user.tenant_id, category_id, req.name, req.description)
    except ResourceNotFoundException as e:
        raise HTTPException(404, detail="Category not found") from e
    except CategoryAlreadyExists as e:
        raise HTTPException(409, detail="Category already exists") from e

    return JSONResponse({"data": asdict(category)})
