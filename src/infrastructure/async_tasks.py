import datetime
import inspect
from collections.abc import Callable

from pydantic import BaseModel

from domain.entities import MessageAuthor
from domain.exceptions import MessageNotFoundException
from domain.ports.repositories import MessageRepository
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository
from domain.ports.services import AIAgentService
from domain.ports.services import AMQPService
from infrastructure.async_tasks import async_task
from infrastructure.async_tasks.ai import run_agent
from infrastructure.async_tasks.realtime import notify_user
from infrastructure.config.settings import app_settings
from infrastructure.di import resolve


class WhatsappMessage(BaseModel):
    message_body: str
    phone_number: str


class IncomingWhatsappMessage(WhatsappMessage):
    message_id: str
    timestamp: datetime.datetime


class AsyncTask:
    def __init__(self, routing_key: str, func: Callable):
        self._amqp_service = None
        self._func = func
        self._routing_key = routing_key
        self._func_module = inspect.getmodule(func).__name__
        self._func_name = func.__name__

    async def __call__(self, *args, **kwargs):
        return await self._func(*args, **kwargs)

    async def delay(self, **kwargs):
        message = {
            "module": self._func_module,
            "func": self._func_name,
            "kwargs": kwargs,
        }

        amqp_service = await resolve(AMQPService)
        await amqp_service.publish(message, self._routing_key)


def async_task(func: Callable) -> AsyncTask:
    return AsyncTask(app_settings.async_task_routing_key, func)


@async_task
async def notify_user(message_id: int):
    # TODO: notify user using websocket
    return


@async_task
async def run_agent(message_body: str, user_id: int):
    ai_agent_service: AIAgentService = await resolve(AIAgentService)
    user_repo: UserRepository = await resolve(UserRepository)
    message_repo: MessageRepository = await resolve(MessageRepository)

    user = user_repo.get_by_id(user_id)
    answer = await ai_agent_service.run(message_body, user)

    timestamp = datetime.datetime.now(datetime.UTC)

    message = message_repo.create(answer, MessageAuthor.BILLY.value, timestamp, user.id, user.tenant_id)

    await process_message.delay(message_id=message.id)


@async_task
async def process_message(message_id: int):
    message_repo: MessageRepository = await resolve(MessageRepository)

    try:
        message = message_repo.get_by_id(message_id)
    except MessageNotFoundException:
        return

    await notify_user.delay(message_id=message.id)

    if message.author == MessageAuthor.USER.value:
        await run_agent.delay(message_body=message.body, user_id=message.user_id)


@async_task
async def process_incoming_message(payload: dict):
    message_repo: MessageRepository = await resolve(MessageRepository)
    user_repo: UserRepository = await resolve(UserRepository)
    tenant_repo: TenantRepository = await resolve(TenantRepository)

    whatsapp_message = IncomingWhatsappMessage(**payload)

    user = user_repo.get_by_phone_number(whatsapp_message.phone_number)

    if user is None:
        tenant = tenant_repo.create()
        user = user_repo.create(
            phone_number=whatsapp_message.phone_number,
            name="",
            tenant_id=tenant.id,
            registered=False,
        )

    message = message_repo.create(
        body=whatsapp_message.message_body,
        author=MessageAuthor.USER.value,
        timestamp=whatsapp_message.timestamp,
        user_id=user.id,
        tenant_id=user.tenant_id,
    )

    await process_message.delay(message_id=message.id)


@async_task
async def send_message(message_id: int):
    amqp_service: AMQPService = await resolve(AMQPService)
    message_repo: MessageRepository = await resolve(MessageRepository)
    user_repo: UserRepository = await resolve(UserRepository)

    message = message_repo.get_by_id(message_id=message_id)
    user = user_repo.get_by_id(message.user_id)

    whatsapp_message = WhatsappMessage(message_body=message.body, phone_number=user.phone_number)

    await amqp_service.publish(
        message=whatsapp_message.model_dump(),
        queue_name=app_settings.whatsapp_message_routing_key,
    )
