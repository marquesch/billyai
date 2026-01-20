import asyncio
import datetime

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


# TODO: Improve async_task_service to distribute between multiple use cases
# each with their own dependencies.
class AsyncTaskService:
    def __init__(
        self,
        async_task_dispatcher: AsyncTaskDispatcherService,
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

        await self._async_task_dispatcher.dispatch("process_message", message_id=message.id)

    async def process_message(self, message_id: int):
        await asyncio.sleep(2)
        try:
            message = self._message_repo.get_by_id(message_id)
        except MessageNotFoundException:
            return

        await self._async_task_dispatcher.dispatch("notify_user", message_id=message.id)

        if message.author == MessageAuthor.USER.value:
            await self._async_task_dispatcher.dispatch("run_agent", message_id=message.id)
        elif message.broker == MessageBroker.WHATSAPP.value:
            await self._async_task_dispatcher.dispatch("send_message", messaeg_id=message.id)

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

        await self._async_task_dispatcher.dispatch("process_message", message_id=reply_msg.id)

    async def send_message(self, message_id: int):
        message = self._message_repo.get_by_id(message_id=message_id)
        user = self._user_repo.get_by_id(message.user_id)

        await self._whatsapp_broker_message_service.send_message(message.body, user.phone_number)
