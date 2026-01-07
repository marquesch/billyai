import datetime

from domain.entities import MessageAuthor
from domain.ports.repositories import MessageRepository
from domain.ports.repositories import UserRepository
from domain.ports.services import AIAgentService
from infrastructure.async_tasks import async_task
from infrastructure.di import resolve


@async_task
async def run_agent(message_body: str, user_id: int):
    ai_agent_service: AIAgentService = await resolve(AIAgentService)
    user_repo: UserRepository = await resolve(UserRepository)
    message_repo: MessageRepository = await resolve(MessageRepository)

    user = user_repo.get_by_id(user_id)
    answer = await ai_agent_service.run(message_body, phone_number)

    timestamp = datetime.datetime.now(datetime.UTC)

    message_repo.create(answer, MessageAuthor.BILLY.value, timestamp, user.id, user.tenant_id)
