import datetime
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel

from domain.entities import MessageAuthor
from domain.entities import User
from domain.ports.repositories import MessageRepository
from infrastructure.async_tasks.ai_tasks import run_agent
from presentation.api import dependencies

router = APIRouter(prefix="/messages")


class MessageRequest(BaseModel):
    body: str


@router.get("/")
def index(
    user: Annotated[User, Depends(dependencies.get_current_user)],
    message_repository: Annotated[MessageRepository, Depends(dependencies.get_message_repository)],
):
    return [message for message in message_repository.get_all(user_id=user.id, tenant_id=user.tenant_id)]


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
        external_message_id=None,
    )

    await run_agent.delay(message_body=message.body, phone_number=user.phone_number)

    return message
