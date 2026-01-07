import datetime

from application.use_cases.message.process_message import SaveMessageUseCase
from domain.entities import MessageAuthor
from domain.exceptions import MessageNotFoundException
from domain.ports.repositories import MessageRepository
from infrastructure.async_tasks import async_task
from infrastructure.async_tasks.ai import run_agent
from infrastructure.async_tasks.realtime import notify_user
from infrastructure.di import resolve


@async_task
async def save_message(message_body: str, author: str, user_id: int, tenant_id: int):
    print("running save_message task")
    save_message_use_case: SaveMessageUseCase = await resolve(SaveMessageUseCase)
    timestamp = datetime.datetime.now()
    save_message_use_case(message_body, author, timestamp, user_id, tenant_id)
    print("done running save_message task")


@async_task
async def process_message(message_id: int):
    message_repo: MessageRepository = await resolve(MessageRepository)

    try:
        message = message_repo.get_by_id(message_id)
    except MessageNotFoundException:
        return

    await notify_user(message.id)

    if message.author == MessageAuthor.USER:
        await run_agent.delay(message_body=message.body, user_id=message.user_id)
