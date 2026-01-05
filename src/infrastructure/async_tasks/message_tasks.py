import datetime

from domain.exceptions import MessageNotFoundException
from domain.ports.repositories import MessageRepository
from infrastructure.async_tasks import async_task
from infrastructure.di import resolve


@async_task
async def save_message(message_body: str, author: str, user_id: int, tenant_id: int):
    print("running save_message task")
    message_repo: MessageRepository = await resolve(MessageRepository)
    timestamp = datetime.datetime.now()
    message_repo.create(message_body, author, timestamp, user_id, tenant_id)
    print("done running save_message task")


@async_task
async def process_message(message_id: int):
    message_repo: MessageRepository = await resolve(MessageRepository)

    try:
        message = message_repo.get_by_id(message_id)
    except MessageNotFoundException:
        return

    # TODO send websocket events
