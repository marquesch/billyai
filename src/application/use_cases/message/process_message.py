import datetime

from domain.entities import MessageAuthor
from domain.entities import User
from domain.ports.repositories import MessageRepository


class SaveMessageUseCase:
    def __init__(self, message_repository: MessageRepository):
        self._message_repository = message_repository

    def __call__(
        self,
        user: User,
        message_body: str,
        author: MessageAuthor,
        timestamp: datetime.datetime,
        message_external_id: str,
    ):
        return self._message_repository.create(
            message_body,
            author,
            timestamp,
            user.id,
            user.tenant_id,
            message_external_id,
        )
