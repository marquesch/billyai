import asyncio
import datetime
from collections.abc import Callable
from typing import Any
from typing import Generic
from typing import TypeVar

from domain.entities import MessageAuthor
from domain.entities import MessageBroker
from domain.exceptions import MessageNotFoundException
from domain.ports.repositories import MessageRepository
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository
from domain.ports.services import AIAgentService
from domain.ports.services import AsyncTaskDispatcher
from domain.ports.services import PubsubService
from domain.ports.services import WhatsappBrokerMessageService

T = TypeVar("T")


class BoundTask(Generic[T]):
    def __init__(self, instance: Any, func: Callable[..., T], name: str):
        self._instance = instance
        self._func = func
        self._task_name = name

    async def __call__(self, *args, **kwargs) -> T:
        return await self._func(self._instance, *args, **kwargs)

    async def delay(self, **kwargs) -> None:
        await self._instance._async_task_dispatcher.dispatch(self._task_name, **kwargs)


class Task:
    def __init__(self, func: Callable):
        self._func = func
        self._name = func.__name__

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return BoundTask(instance, self._func, self._name)


def task(func):
    return Task(func)


class AsyncTaskService:
    def __init__(
        self,
        async_task_dispatcher: AsyncTaskDispatcher,
        message_repo: MessageRepository,
        user_repo: UserRepository,
        tenant_repo: TenantRepository,
        ai_agent_service: AIAgentService,
        pubsub_service: PubsubService,
        whatsapp_broker_message_service: WhatsappBrokerMessageService,
    ):
        self._async_task_dispatcher = async_task_dispatcher
        self._message_repo = message_repo
        self._user_repo = user_repo
        self._tenant_repo = tenant_repo
        self._ai_agent = ai_agent_service
        self._pubsub = pubsub_service
        self._whatsapp_broker_message_service = whatsapp_broker_message_service

    @task
    async def process_incoming_message(
        self,
        message_body: str,
        phone_number: str,
        timestamp: str,
        message_id: str | None = None,
    ):
        dt_timestamp = datetime.datetime.fromisoformat(timestamp)

        user = self._user_repo.get_by_phone_number(phone_number)
        if user is None:
            tenant = self._tenant_repo.create()
            user = self._user_repo.create(
                phone_number=phone_number,
                name="",
                tenant_id=tenant.id,
                is_registered=False,
            )

        message = self._message_repo.create(
            body=message_body,
            author=MessageAuthor.USER,
            timestamp=dt_timestamp,
            broker=MessageBroker.WHATSAPP,
            user_id=user.id,
            tenant_id=user.tenant_id,
            external_message_id=message_id,
        )

        await self.process_message.delay(message_id=message.id)

    @task
    async def process_message(self, message_id: int):
        await asyncio.sleep(2)
        try:
            message = self._message_repo.get_by_id(message_id)
        except MessageNotFoundException:
            return

        await self.notify_user.delay(message_id=message.id)

        if message.author == MessageAuthor.USER.value:
            await self.run_agent.delay(message_id=message.id)
        elif message.broker == MessageBroker.WHATSAPP.value:
            await self.send_message.delay(message_id=message.id)

    @task
    async def notify_user(self, message_id: int):
        message = self._message_repo.get_by_id(message_id)
        message_data = {
            "id": message.id,
            "author": message.author,
            "body": message.body,
            "timestamp": message.timestamp.isoformat(),
            "broker": message.broker,
        }
        await self._pubsub.publish(channel=str(message.tenant_id), event="new-message", data=message_data)

    @task
    async def run_agent(self, message_id: int):
        message = self._message_repo.get_by_id(message_id)
        user = self._user_repo.get_by_id(message.user_id)

        answer = await self._ai_agent.run(message.body, user)

        reply_msg = self._message_repo.create(
            body=answer,
            author=MessageAuthor.BILLY,
            timestamp=datetime.datetime.now(datetime.UTC),
            broker=message.broker,
            user_id=user.id,
            tenant_id=user.tenant_id,
        )

        await self.process_message.delay(message_id=reply_msg.id)

    @task
    async def send_message(self, message_id: int):
        message = self._message_repo.get_by_id(message_id=message_id)
        user = self._user_repo.get_by_id(message.user_id)

        await self._whatsapp_broker_message_service.send_message(message.body, user.phone_number)
