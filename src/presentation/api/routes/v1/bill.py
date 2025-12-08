import datetime
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from domain.entities import User
from domain.exceptions import BillNotFoundException
from domain.exceptions import CategoryNotFoundException
from domain.ports.repositories import BillRepository
from domain.ports.repositories import CategoryRepository
from presentation.api import dependencies

router = APIRouter(prefix="/bills")


class BillRequest(BaseModel):
    date: datetime.datetime
    value: float
    category_id: int | None


@router.get("/")
def index(
    user: Annotated[User, Depends(dependencies.get_current_user)],
    bill_repository: Annotated[BillRepository, Depends(dependencies.get_bill_repository)],
):
    bills = [bill for bill in bill_repository.get_many(tenant_id=user.tenant_id)]

    return bills


@router.get("/{bill_id}")
def get_bill(
    bill_id: int,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    bill_repository: Annotated[BillRepository, Depends(dependencies.get_bill_repository)],
):
    try:
        bill = bill_repository.get_by_id(user.tenant_id, bill_id)
    except BillNotFoundException:
        raise HTTPException(404, detail="Bill not found")

    return bill


@router.post("/", status_code=201)
def create_bill(
    req: BillRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    bill_repository: Annotated[BillRepository, Depends(dependencies.get_bill_repository)],
    category_repository: Annotated[CategoryRepository, Depends(dependencies.get_category_repository)],
):
    if req.category_id is not None:
        try:
            category = category_repository.get_by_id(user.tenant_id, req.category_id)
        except CategoryNotFoundException:
            raise HTTPException(404, detail="Category not found")

    return bill_repository.create(user.tenant_id, date=req.date, value=req.value, category_id=req.category_id)


@router.put("/{bill_id}")
def update_bill(
    bill_id: int,
    req: BillRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    bill_repository: Annotated[BillRepository, Depends(dependencies.get_bill_repository)],
    category_repository: Annotated[CategoryRepository, Depends(dependencies.get_category_repository)],
):
    if req.category_id is not None:
        try:
            category = category_repository.get_by_id(user.tenant_id, req.category_id)
        except CategoryNotFoundException:
            raise HTTPException(404, detail="Category not found")

    try:
        bill = bill_repository.update(user.tenant_id, bill_id, req.date, req.value, req.category_id)
    except BillNotFoundException:
        raise HTTPException(404, detail="Bill not found")

    return bill
