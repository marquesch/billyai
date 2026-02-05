import datetime
from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from domain.entities import Message
from domain.entities import MessageAuthor
from domain.entities import MessageBroker
from domain.exceptions import MessageNotFoundException
from infrastructure.persistence.database.models import DBMessage
from infrastructure.persistence.database.models import DBTenant
from infrastructure.persistence.database.models import DBUser
from infrastructure.persistence.database.repositories.message_repository import DBMessageRepository


class TestDBMessageRepositoryCreate:
    def test_create_message_successfully(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        body = "Hello, this is a test message"
        author = MessageAuthor.USER
        timestamp = datetime.datetime(2025, 1, 20, 10, 30, 0)
        broker = MessageBroker.WHATSAPP
        external_message_id = "ext_msg_12345"

        message = db_message_repository.create(
            body=body,
            author=author,
            timestamp=timestamp,
            broker=broker,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
            external_message_id=external_message_id,
        )

        assert isinstance(message, Message)
        assert message.body == body
        assert message.author == author
        assert message.timestamp == timestamp
        assert message.broker == broker
        assert message.user_id == db_user.id
        assert message.tenant_id == db_tenant.id
        assert message.external_message_id == external_message_id
        assert message.id is not None

    def test_create_message_without_external_id(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        body = "Message without external ID"
        author = MessageAuthor.USER
        timestamp = datetime.datetime(2025, 1, 20, 10, 30, 0)
        broker = MessageBroker.WHATSAPP

        message = db_message_repository.create(
            body=body,
            author=author,
            timestamp=timestamp,
            broker=broker,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
            external_message_id=None,
        )

        assert message.external_message_id is None

    def test_create_message_with_bot_author(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        body = "Bot response"
        author = MessageAuthor.BILLY
        timestamp = datetime.datetime(2025, 1, 20, 10, 30, 0)
        broker = MessageBroker.WHATSAPP

        message = db_message_repository.create(
            body=body,
            author=author,
            timestamp=timestamp,
            broker=broker,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
        )

        assert message.author == MessageAuthor.BILLY

    def test_create_message_with_empty_body(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        body = ""
        author = MessageAuthor.USER
        timestamp = datetime.datetime(2025, 1, 20, 10, 30, 0)
        broker = MessageBroker.WHATSAPP

        message = db_message_repository.create(
            body=body,
            author=author,
            timestamp=timestamp,
            broker=broker,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
        )

        assert message.body == ""

    def test_create_message_with_very_long_body(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        body = "A" * 5000
        author = MessageAuthor.USER
        timestamp = datetime.datetime(2025, 1, 20, 10, 30, 0)
        broker = MessageBroker.WHATSAPP

        message = db_message_repository.create(
            body=body,
            author=author,
            timestamp=timestamp,
            broker=broker,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
        )

        assert message.body == body


class TestDBMessageRepositoryGetAll:
    def test_get_all_messages_for_user(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
        db_messages: list[DBMessage],
    ):
        messages = list(
            db_message_repository.get_all(user_id=db_user.id, tenant_id=db_tenant.id),
        )

        assert len(messages) == 4
        assert all(isinstance(message, Message) for message in messages)
        assert all(message.user_id == db_user.id for message in messages)
        assert all(message.tenant_id == db_tenant.id for message in messages)

    def test_get_all_messages_ordered_by_timestamp_desc(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
        db_messages: list[DBMessage],
    ):
        messages = list(
            db_message_repository.get_all(user_id=db_user.id, tenant_id=db_tenant.id),
        )

        timestamps = [msg.timestamp for msg in messages]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_all_messages_returns_generator(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
        db_messages: list[DBMessage],
    ):
        result = db_message_repository.get_all(
            user_id=db_user.id,
            tenant_id=db_tenant.id,
        )

        assert isinstance(result, Generator)
        messages = list(result)
        assert len(messages) == 4

    def test_get_all_messages_for_user_with_no_messages(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        messages = list(
            db_message_repository.get_all(user_id=db_user.id, tenant_id=db_tenant.id),
        )

        assert len(messages) == 0

    def test_get_all_messages_filters_by_user(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        another_db_user: DBUser,
        db_tenant: DBTenant,
        db_messages: list[DBMessage],
    ):
        messages = list(
            db_message_repository.get_all(user_id=db_user.id, tenant_id=db_tenant.id),
        )

        assert len(messages) == 4
        assert all(message.user_id == db_user.id for message in messages)

    def test_get_all_messages_filters_by_tenant(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
        another_db_tenant: DBTenant,
        db_messages: list[DBMessage],
    ):
        messages = list(
            db_message_repository.get_all(user_id=db_user.id, tenant_id=db_tenant.id),
        )

        assert len(messages) == 4
        assert all(message.tenant_id == db_tenant.id for message in messages)


class TestDBMessageRepositoryGetById:
    def test_get_existing_message(
        self,
        db_message_repository: DBMessageRepository,
        db_sample_message: DBMessage,
    ):
        message = db_message_repository.get_by_id(message_id=db_sample_message.id)

        assert isinstance(message, Message)
        assert message.id == db_sample_message.id
        assert message.body == db_sample_message.body
        assert message.author == db_sample_message.author
        assert message.timestamp == db_sample_message.timestamp
        assert message.broker == db_sample_message.broker
        assert message.user_id == db_sample_message.user_id
        assert message.tenant_id == db_sample_message.tenant_id

    def test_get_nonexistent_message(self, db_message_repository: DBMessageRepository):
        with pytest.raises(MessageNotFoundException):
            db_message_repository.get_by_id(message_id=99999)


class TestDBMessageRepositoryEdgeCases:
    def test_create_message_with_past_timestamp(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        body = "Old message"
        author = MessageAuthor.USER
        timestamp = datetime.datetime(2020, 1, 1, 0, 0, 0)
        broker = MessageBroker.WHATSAPP

        message = db_message_repository.create(
            body=body,
            author=author,
            timestamp=timestamp,
            broker=broker,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
        )

        assert message.timestamp == timestamp

    def test_create_message_with_future_timestamp(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        body = "Future message"
        author = MessageAuthor.USER
        timestamp = datetime.datetime(2030, 12, 31, 23, 59, 59)
        broker = MessageBroker.WHATSAPP

        message = db_message_repository.create(
            body=body,
            author=author,
            timestamp=timestamp,
            broker=broker,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
        )

        assert message.timestamp == timestamp

    def test_create_multiple_messages_same_user(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        base_timestamp = datetime.datetime(2025, 1, 20, 10, 0, 0)

        for i in range(5):
            db_message_repository.create(
                body=f"Message {i}",
                author=MessageAuthor.USER,
                timestamp=base_timestamp + datetime.timedelta(minutes=i),
                broker=MessageBroker.WHATSAPP,
                user_id=db_user.id,
                tenant_id=db_tenant.id,
            )

        messages = list(
            db_message_repository.get_all(user_id=db_user.id, tenant_id=db_tenant.id),
        )

        assert len(messages) == 5

    def test_create_message_with_different_brokers(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
    ):
        brokers = [MessageBroker.WHATSAPP, MessageBroker.API]
        timestamp = datetime.datetime(2025, 1, 20, 10, 0, 0)

        for broker in brokers:
            message = db_message_repository.create(
                body=f"Message via {broker}",
                author=MessageAuthor.USER,
                timestamp=timestamp,
                broker=broker,
                user_id=db_user.id,
                tenant_id=db_tenant.id,
            )
            assert message.broker == broker

    def test_get_all_with_mixed_authors(
        self,
        db_message_repository: DBMessageRepository,
        db_user: DBUser,
        db_tenant: DBTenant,
        session: Session,
    ):
        timestamp = datetime.datetime(2025, 1, 20, 10, 0, 0)

        db_message_repository.create(
            body="User message 1",
            author=MessageAuthor.USER,
            timestamp=timestamp,
            broker=MessageBroker.WHATSAPP,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
        )

        db_message_repository.create(
            body="Bot response",
            author=MessageAuthor.SYSTEM,
            timestamp=timestamp + datetime.timedelta(minutes=1),
            broker=MessageBroker.WHATSAPP,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
        )

        db_message_repository.create(
            body="User message 2",
            author=MessageAuthor.USER,
            timestamp=timestamp + datetime.timedelta(minutes=2),
            broker=MessageBroker.WHATSAPP,
            user_id=db_user.id,
            tenant_id=db_tenant.id,
        )

        messages = list(
            db_message_repository.get_all(user_id=db_user.id, tenant_id=db_tenant.id),
        )

        assert len(messages) == 3
        assert messages[0].author == MessageAuthor.USER
        # assert messages[1].author == "OPT"
        assert messages[2].author == MessageAuthor.USER
