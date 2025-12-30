import datetime

from domain.ports.repositories import MessageRepository
from infrastructure.async_tasks import task
from infrastructure.di import resolve


@task
async def save_message(message_body: str, author: str, user_id: int, tenant_id: int):
    print("running save_message task")
    message_repo: MessageRepository = await resolve(MessageRepository)
    timestamp = datetime.datetime.now()
    message_repo.create(message_body, author, timestamp, user_id, tenant_id)
    print("done running save_message task")
