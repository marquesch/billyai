from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from domain.entities import User
from domain.exceptions import UserNotFoundException
from domain.ports.repositories import UserRepository
from presentation.api import dependencies

router = APIRouter(prefix="/users")


class UserRequest(BaseModel):
    name: str


@router.put("/me")
def update_me(
    req: UserRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    user_repository: Annotated[UserRepository, Depends(dependencies.get_user_repository)],
):
    try:
        return user_repository.update(user.id, user.tenant_id, req.name)
    except UserNotFoundException as e:
        raise HTTPException(404, detail="User not found") from e
