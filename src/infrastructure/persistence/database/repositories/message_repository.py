import datetime
from collections.abc import Generator

from domain.entities import Message
from domain.exceptions import MessageNotFoundException
from infrastructure.persistence.database.models import DBMessage
from infrastructure.persistence.database.repositories import DBRepository


class DBMessageRepository(DBRepository):
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
        message = DBMessage(
            body=body,
            author=author,
            timestamp=timestamp,
            broker=broker,
            user_id=user_id,
            tenant_id=tenant_id,
            external_message_id=external_message_id,
        )

        self.session.add(message)
        self.session.flush()
        self.session.refresh(message)

        return message.to_entity()

    def get_all(self, user_id: int, tenant_id: int) -> Generator[Message]:
        query = (
            self.session.query(DBMessage)
            .filter_by(user_id=user_id, tenant_id=tenant_id)
            .order_by(DBMessage.timestamp.desc())
        )
        return (message.to_entity() for message in query)

    def get_by_id(self, message_id: int) -> Message:
        message = self.session.query(DBMessage).get(message_id)

        if message is None:
            raise MessageNotFoundException

        return message.to_entity()
