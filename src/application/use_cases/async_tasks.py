import asyncio
import datetime

from application.use_cases import AsyncTask
from domain.entities import MessageAuthor
from domain.entities import MessageBroker
from domain.exceptions import MessageNotFoundException
from domain.ports.repositories import MessageRepository
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository
from domain.ports.services import AIAgentService
from domain.ports.services import AsyncTaskDispatcherService
from domain.ports.services import PubsubService
from domain.ports.services import WhatsappBrokerMessageService


class ProcessIncomingMessage(AsyncTask):
    dependencies = [AsyncTaskDispatcherService, MessageRepository, UserRepository, TenantRepository]

    def __init__(
        self,
        async_task_dispatcher: AsyncTaskDispatcherService,
        message_repository: MessageRepository,
        user_repository: UserRepository,
        tenant_repository: TenantRepository,
    ):
        self._async_task_dispatcher = async_task_dispatcher
        self._message_repository = message_repository
        self._user_repository = user_repository
        self._tenant_repository = tenant_repository

    async def __call__(
        self,
        message_body: str,
        phone_number: str,
        timestamp: str,
        message_id: str | None = None,
    ):
        dt_timestamp = datetime.datetime.fromisoformat(timestamp)
        user = self._user_repository.get_by_phone_number(phone_number)
        if user is None:
            tenant = self._tenant_repository.create()
            user = self._user_repository.create(
                phone_number=phone_number,
                name="",
                tenant_id=tenant.id,
                is_registered=False,
            )
        message = self._message_repository.create(
            body=message_body,
            author=MessageAuthor.USER,
            timestamp=dt_timestamp,
            broker=MessageBroker.WHATSAPP,
            user_id=user.id,
            tenant_id=user.tenant_id,
            external_message_id=message_id,
        )
        await ProcessMessage.dispatch(self._async_task_dispatcher, message_id=message.id)


class ProcessMessage(AsyncTask):
    dependencies = [AsyncTaskDispatcherService, MessageRepository]

    def __init__(
        self,
        async_task_dispatcher: AsyncTaskDispatcherService,
        message_repository: MessageRepository,
    ):
        self._async_task_dispatcher = async_task_dispatcher
        self._message_repository = message_repository

    async def __call__(self, message_id: int):
        await asyncio.sleep(2)
        try:
            message = self._message_repository.get_by_id(message_id)
        except MessageNotFoundException:
            return
        await NotifyUser.dispatch(self._async_task_dispatcher, message_id=message.id)
        if message.author == MessageAuthor.USER.value:
            await RunAgent.dispatch(self._async_task_dispatcher, message_id=message.id)
        elif message.broker == MessageBroker.WHATSAPP.value:
            await SendMessage.dispatch(self._async_task_dispatcher, message_id=message.id)


class NotifyUser(AsyncTask):
    dependencies = [MessageRepository, PubsubService]

    def __init__(
        self,
        message_repository: MessageRepository,
        pubsub_service: PubsubService,
    ):
        self._message_repository = message_repository
        self._pubsub_service = pubsub_service

    async def __call__(self, message_id: int):
        message = self._message_repository.get_by_id(message_id)
        message_data = {
            "id": message.id,
            "author": message.author,
            "body": message.body,
            "timestamp": message.timestamp.isoformat(),
            "broker": message.broker,
        }
        await self._pubsub_service.publish(channel=str(message.tenant_id), event="new-message", data=message_data)


class RunAgent(AsyncTask):
    dependencies = AsyncTaskDispatcherService, MessageRepository, UserRepository, AIAgentService

    def __init__(
        self,
        async_task_dispatcher: AsyncTaskDispatcherService,
        message_repository: MessageRepository,
        user_repository: UserRepository,
        ai_agent_service: AIAgentService,
    ):
        self._async_task_dispatcher = async_task_dispatcher
        self._message_repository = message_repository
        self._user_repository = user_repository
        self._ai_agent_service = ai_agent_service

    async def __call__(self, message_id: int):
        message = self._message_repository.get_by_id(message_id)
        user = self._user_repository.get_by_id(message.user_id)
        answer = await self._ai_agent_service.run(message.body, user)
        reply_msg = self._message_repository.create(
            body=answer,
            author=MessageAuthor.BILLY,
            timestamp=datetime.datetime.now(datetime.UTC),
            broker=message.broker,
            user_id=user.id,
            tenant_id=user.tenant_id,
        )
        await ProcessMessage.dispatch(self._async_task_dispatcher, message_id=reply_msg.id)


class SendMessage(AsyncTask):
    dependencies = [MessageRepository, UserRepository, WhatsappBrokerMessageService]

    def __init__(
        self,
        message_repository: MessageRepository,
        user_repository: UserRepository,
        whatsapp_broker_message_service: WhatsappBrokerMessageService,
    ):
        self._message_repository = message_repository
        self._user_repository = user_repository
        self._whatsapp_broker_message_service = whatsapp_broker_message_service

    async def __call__(self, message_id: int):
        message = self._message_repository.get_by_id(message_id=message_id)
        user = self._user_repository.get_by_id(message.user_id)
        await self._whatsapp_broker_message_service.send_message(message.body, user.phone_number)
