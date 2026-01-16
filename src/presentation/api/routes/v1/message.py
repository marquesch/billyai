import datetime
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel

from domain.entities import MessageAuthor
from domain.entities import MessageBroker
from domain.entities import User
from domain.ports.repositories import MessageRepository
from infrastructure.async_tasks import process_message
from presentation.api import dependencies

router = APIRouter(prefix="/messages")


class MessageRequest(BaseModel):
    body: str


@router.get("/")
def index(
    user: Annotated[User, Depends(dependencies.get_current_user)],
    message_repository: Annotated[MessageRepository, Depends(dependencies.get_message_repository)],
):
    return list(message_repository.get_all(user_id=user.id, tenant_id=user.tenant_id))


@router.post("/")
async def create(
    req: MessageRequest,
    user: Annotated[User, Depends(dependencies.get_current_user)],
    message_repository: Annotated[MessageRepository, Depends(dependencies.get_message_repository)],
):
    message = message_repository.create(
        body=req.body,
        author=MessageAuthor.USER,
        timestamp=datetime.datetime.now(),
        user_id=user.id,
        tenant_id=user.tenant_id,
        broker=MessageBroker.API.value,
        external_message_id=None,
    )

    await process_message.delay(message_id=message.id)

    return message
