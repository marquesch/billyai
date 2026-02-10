import datetime
from unittest.mock import AsyncMock

import pytest

from application.use_cases.async_tasks import NotifyUser
from application.use_cases.async_tasks import ProcessIncomingMessage
from application.use_cases.async_tasks import ProcessMessage
from application.use_cases.async_tasks import RunAgent
from application.use_cases.async_tasks import SendMessage
from domain.entities import Message
from domain.entities import MessageAuthor
from domain.entities import MessageBroker
from domain.entities import User
from domain.exceptions import MessageNotFoundException
from infrastructure.persistence.memory.repositories.message_repository import InMemoryMessageRepository
from infrastructure.persistence.memory.repositories.tenant_repository import InMemoryTenantRepository
from infrastructure.persistence.memory.repositories.user_repository import InMemoryUserRepository


@pytest.fixture
def process_incoming_message_use_case(
    mock_async_task_dispatcher: AsyncMock,
    in_memory_message_repository: InMemoryMessageRepository,
    in_memory_user_repository: InMemoryUserRepository,
    in_memory_tenant_repository: InMemoryTenantRepository,
) -> ProcessIncomingMessage:
    return ProcessIncomingMessage(
        async_task_dispatcher=mock_async_task_dispatcher,
        message_repository=in_memory_message_repository,
        user_repository=in_memory_user_repository,
        tenant_repository=in_memory_tenant_repository,
    )


@pytest.fixture
def process_message_use_case(
    mock_async_task_dispatcher: AsyncMock,
    in_memory_message_repository: InMemoryMessageRepository,
) -> ProcessMessage:
    return ProcessMessage(
        async_task_dispatcher=mock_async_task_dispatcher,
        message_repository=in_memory_message_repository,
    )


@pytest.fixture
def notify_user_use_case(
    in_memory_message_repository: InMemoryMessageRepository,
    mock_pubsub_service: AsyncMock,
) -> NotifyUser:
    return NotifyUser(
        message_repository=in_memory_message_repository,
        pubsub_service=mock_pubsub_service,
    )


@pytest.fixture
def run_agent_use_case(
    mock_async_task_dispatcher: AsyncMock,
    in_memory_message_repository: InMemoryMessageRepository,
    in_memory_user_repository: InMemoryUserRepository,
    mock_ai_agent_service: AsyncMock,
) -> RunAgent:
    return RunAgent(
        async_task_dispatcher=mock_async_task_dispatcher,
        message_repository=in_memory_message_repository,
        user_repository=in_memory_user_repository,
        ai_agent_service=mock_ai_agent_service,
    )


@pytest.fixture
def send_message_use_case(
    in_memory_message_repository: InMemoryMessageRepository,
    in_memory_user_repository: InMemoryUserRepository,
    mock_whatsapp_service: AsyncMock,
) -> SendMessage:
    return SendMessage(
        message_repository=in_memory_message_repository,
        user_repository=in_memory_user_repository,
        whatsapp_broker_message_service=mock_whatsapp_service,
    )


class TestProcessIncomingMessage:
    @pytest.mark.asyncio
    async def test_process_incoming_message_use_case_for_existing_user(
        self,
        process_incoming_message_use_case: ProcessIncomingMessage,
        in_memory_user_repository: InMemoryUserRepository,
        in_memory_message_repository: InMemoryMessageRepository,
        in_memory_registered_user: User,
    ):
        message_body = "Hello"
        phone_number = in_memory_registered_user.phone_number
        timestamp = "2025-01-20T10:30:00"
        message_id = "ext_msg_123"

        await process_incoming_message_use_case(
            message_body=message_body,
            phone_number=phone_number,
            timestamp=timestamp,
            message_id=message_id,
        )

        messages = list(
            in_memory_message_repository.get_all(
                user_id=in_memory_registered_user.id,
                tenant_id=in_memory_registered_user.tenant_id,
            ),
        )

        assert len(messages) == 1
        assert messages[0].body == message_body
        assert messages[0].author == MessageAuthor.USER
        assert messages[0].broker == MessageBroker.WHATSAPP
        assert messages[0].user_id == in_memory_registered_user.id
        assert messages[0].tenant_id == in_memory_registered_user.tenant_id
        assert messages[0].external_message_id == message_id

    @pytest.mark.asyncio
    async def test_process_incoming_message_use_case_for_new_user(
        self,
        process_incoming_message_use_case: ProcessIncomingMessage,
        in_memory_user_repository: InMemoryUserRepository,
        in_memory_tenant_repository: InMemoryTenantRepository,
        in_memory_message_repository: InMemoryMessageRepository,
    ):
        message_body = "Hello"
        phone_number = "+5511987654321"
        timestamp = "2025-01-20T10:30:00"
        message_id = "ext_msg_456"

        await process_incoming_message_use_case(
            message_body=message_body,
            phone_number=phone_number,
            timestamp=timestamp,
            message_id=message_id,
        )

        user = in_memory_user_repository.get_by_phone_number(phone_number)
        assert user is not None
        assert user.phone_number == phone_number
        assert user.name == ""
        assert user.is_registered is False

        messages = list(in_memory_message_repository.get_all(user_id=user.id, tenant_id=user.tenant_id))
        assert len(messages) == 1
        assert messages[0].body == message_body

    @pytest.mark.asyncio
    async def test_process_incoming_message_use_case_without_external_id(
        self,
        process_incoming_message_use_case: ProcessIncomingMessage,
        in_memory_message_repository: InMemoryMessageRepository,
        in_memory_registered_user: User,
    ):
        message_body = "Hello"
        phone_number = in_memory_registered_user.phone_number
        timestamp = "2025-01-20T10:30:00"

        await process_incoming_message_use_case(
            message_body=message_body,
            phone_number=phone_number,
            timestamp=timestamp,
            message_id=None,
        )

        messages = list(
            in_memory_message_repository.get_all(
                user_id=in_memory_registered_user.id,
                tenant_id=in_memory_registered_user.tenant_id,
            ),
        )
        assert len(messages) == 1
        assert messages[0].external_message_id is None


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_process_message_use_case_from_user(
        self,
        process_message_use_case: ProcessMessage,
        mock_async_task_dispatcher,
        in_memory_message_from_user: Message,
    ):
        await process_message_use_case(message_id=in_memory_message_from_user.id)

        assert mock_async_task_dispatcher.dispatch.call_count == 2

    @pytest.mark.asyncio
    async def test_process_message_use_case_from_bot_with_whatsapp_broker(
        self,
        process_message_use_case: ProcessMessage,
        mock_async_task_dispatcher,
        in_memory_message_from_bot: Message,
    ):
        await process_message_use_case(message_id=in_memory_message_from_bot.id)

        assert mock_async_task_dispatcher.dispatch.call_count == 2

    @pytest.mark.asyncio
    async def test_process_message_use_case_not_found(
        self,
        process_message_use_case: ProcessMessage,
        mock_async_task_dispatcher,
    ):
        with pytest.raises(MessageNotFoundException):
            await process_message_use_case(message_id=99999)

        mock_async_task_dispatcher.dispatch.assert_not_called()


class TestNotifyUser:
    @pytest.mark.asyncio
    async def test_notify_user_use_case_publishes_message(
        self,
        notify_user_use_case: NotifyUser,
        mock_pubsub_service,
        in_memory_message_from_user: Message,
    ):
        await notify_user_use_case(message_id=in_memory_message_from_user.id)

        mock_pubsub_service.publish.assert_called_once_with(
            channel=str(in_memory_message_from_user.tenant_id),
            event="new-message",
            data={
                "id": in_memory_message_from_user.id,
                "author": in_memory_message_from_user.author.value,
                "body": in_memory_message_from_user.body,
                "timestamp": in_memory_message_from_user.timestamp.isoformat(),
                "broker": in_memory_message_from_user.broker.value,
            },
        )

    @pytest.mark.asyncio
    async def test_notify_user_use_case_with_different_brokers(
        self,
        notify_user_use_case: NotifyUser,
        mock_pubsub_service,
        in_memory_message_from_bot: Message,
    ):
        await notify_user_use_case(message_id=in_memory_message_from_bot.id)

        call_args = mock_pubsub_service.publish.call_args[1]
        assert call_args["data"]["broker"] == MessageBroker.WHATSAPP.value


class TestRunAgent:
    @pytest.mark.asyncio
    async def test_run_agent_use_case_creates_reply(
        self,
        run_agent_use_case: RunAgent,
        mock_async_task_dispatcher,
        mock_ai_agent_service,
        in_memory_message_repository: InMemoryMessageRepository,
        in_memory_message_from_user: Message,
        in_memory_registered_user: User,
    ):
        ai_response = "This is the AI response"
        mock_ai_agent_service.run.return_value = ai_response

        await run_agent_use_case(message_id=in_memory_message_from_user.id)

        mock_ai_agent_service.run.assert_called_once_with(in_memory_message_from_user.body, in_memory_registered_user)
        mock_async_task_dispatcher.dispatch.assert_called_once()

        messages = list(
            in_memory_message_repository.get_all(
                user_id=in_memory_registered_user.id,
                tenant_id=in_memory_registered_user.tenant_id,
            ),
        )
        reply_messages = [msg for msg in messages if msg.author == MessageAuthor.BILLY]
        assert len(reply_messages) == 1
        assert reply_messages[0].body == ai_response

    @pytest.mark.asyncio
    async def test_run_agent_use_case_creates_message_with_correct_fields(
        self,
        run_agent_use_case: RunAgent,
        mock_ai_agent_service,
        in_memory_message_repository: InMemoryMessageRepository,
        in_memory_message_from_user: Message,
        in_memory_registered_user: User,
    ):
        ai_response = "AI answer"
        mock_ai_agent_service.run.return_value = ai_response

        await run_agent_use_case(message_id=in_memory_message_from_user.id)

        messages = list(
            in_memory_message_repository.get_all(
                user_id=in_memory_registered_user.id,
                tenant_id=in_memory_registered_user.tenant_id,
            ),
        )
        reply_message = [msg for msg in messages if msg.author == MessageAuthor.BILLY][0]

        assert reply_message.body == ai_response
        assert reply_message.author == MessageAuthor.BILLY
        assert reply_message.broker == in_memory_message_from_user.broker
        assert reply_message.user_id == in_memory_registered_user.id
        assert reply_message.tenant_id == in_memory_registered_user.tenant_id
        assert isinstance(reply_message.timestamp, datetime.datetime)


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_send_message_use_case_via_whatsapp(
        self,
        send_message_use_case: SendMessage,
        mock_whatsapp_service,
        in_memory_message_from_bot: Message,
        in_memory_registered_user: User,
    ):
        await send_message_use_case(message_id=in_memory_message_from_bot.id)

        mock_whatsapp_service.send_message.assert_called_once_with(
            in_memory_message_from_bot.body,
            in_memory_registered_user.phone_number,
        )
