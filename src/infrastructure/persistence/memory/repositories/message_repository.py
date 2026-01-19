import datetime
from collections.abc import Generator

from domain.entities import Message
from domain.exceptions import MessageNotFoundException
from domain.exceptions import UserNotFoundException
from infrastructure.persistence.memory.repositories import InMemoryRepository


class InMemoryMessageRepository(InMemoryRepository):
    def create(
        self,
        body: str,
        author: str,
        timestamp: datetime.datetime,
        broker: str,
        user_id: int,
        tenant_id: int,
        external_message_id: str | None = None,
    ) -> Message:
        self._in_memory_database.messages_id_seq += 1

        if (user := self._in_memory_database.users.get(user_id)) is None or user.tenant_id != tenant_id:
            raise UserNotFoundException

        message = Message(
            id=self._in_memory_database.messages_id_seq,
            body=body,
            author=author,
            timestamp=timestamp,
            broker=broker,
            user_id=user_id,
            tenant_id=tenant_id,
            external_message_id=external_message_id,
        )

    def get_all(self, user_id: int, tenant_id: int) -> Generator[Message]:
        return (
            message
            for message in filter(
                lambda message: message.user_id == user_id and message.tenant_id == tenant_id,
                self._in_memory_database.messages.values(),
            )
        )

    def get_by_id(self, message_id: int) -> Message:
        if (message := self._in_memory_database.messages.get(message_id)) is None:
            raise MessageNotFoundException

        return message
