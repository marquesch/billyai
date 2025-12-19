import datetime
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from application.services.bill_service import BillService
from domain.entities import User
from domain.exceptions import BillNotFoundException
from domain.exceptions import CategoryNotFoundException
from presentation.api import dependencies

router = APIRouter(prefix="/bills")


class BillRequest(BaseModel):
    date: datetime.date
    value: float
    category_id: int | None


@router.get("/")
def index(
    user: Annotated[User, Depends(dependencies.get_current_user)],
    bill_service: Annotated[BillService, Depends(dependencies.get_bill_service)],
):
    bills = [bill for bill in bill_service.get_many(tenant_id=user.tenant_id)]

    return bills


@router.get("/{bill_id}")
def get_bill(
    bill_id: int,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    bill_service: Annotated[BillService, Depends(dependencies.get_bill_service)],
):
    try:
        bill = bill_service.get_by_id(user.tenant_id, bill_id)
    except BillNotFoundException:
        raise HTTPException(404, detail="Bill not found")

    return bill


@router.post("/", status_code=201)
def create_bill(
    req: BillRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    bill_service: Annotated[BillService, Depends(dependencies.get_bill_service)],
):
    try:
        return bill_service.create(user.tenant_id, date=req.date, value=req.value, category_id=req.category_id)
    except CategoryNotFoundException:
        raise HTTPException(404, detail="Category not found")


@router.put("/{bill_id}")
def update_bill(
    bill_id: int,
    req: BillRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    bill_service: Annotated[BillService, Depends(dependencies.get_bill_service)],
):
    try:
        return bill_service.update(user.tenant_id, bill_id, req.date, req.value, req.category_id)
    except CategoryNotFoundException:
        raise HTTPException(404, detail="Category not found")
    except BillNotFoundException:
        raise HTTPException(404, detail="Bill not found")
