from typing import Protocol
from typing import runtime_checkable

from domain.entities import User


@runtime_checkable
class UserRepository(Protocol):
    def get_by_phone_number(self, phone_number: str) -> User: ...
