from domain.entities import MessageAuthor
from domain.ports.repositories import UserRepository
from domain.ports.services import AIAgentService
from infrastructure.async_tasks import task
from infrastructure.async_tasks.message_tasks import save_message
from infrastructure.di import resolve


@task
async def run_agent(message_body: str, phone_number: str):
    print("running run_agent task")
    ai_agent_service: AIAgentService = await resolve(AIAgentService)
    user_repo: UserRepository = await resolve(UserRepository)

    user = user_repo.get_by_phone_number(phone_number)
    answer = await ai_agent_service.run(message_body, phone_number)

    await save_message.delay(
        message_body=answer,
        author=MessageAuthor.BILLY.value,
        user_id=user.id,
        tenant_id=user.tenant_id,
    )
    print("done running run_agent task")
