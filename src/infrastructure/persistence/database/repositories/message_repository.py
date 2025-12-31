import datetime
from collections.abc import Generator

from domain.entities import Message
from infrastructure.persistence.database.models import DBMessage
from infrastructure.persistence.database.repositories import DBRepository


class DBMessageRepository(DBRepository):
    def create(
        self,
        body: str,
        author: str,
        timestamp: datetime.datetime,
        user_id: int,
        tenant_id: int,
        external_message_id: str | None = None,
    ) -> Message:
        message = DBMessage(
            body=body,
            author=author,
            timestamp=timestamp,
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
