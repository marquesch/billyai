from domain.entities import User
from domain.exceptions import PhoneNumberTakenException
from domain.exceptions import UserNotFoundException
from infrastructure.persistence.memory.repositories import InMemoryRepository


class InMemoryUserRepository(InMemoryRepository):
    def get_by_phone_number(self, phone_number: str) -> User | None:
        users = list(filter(lambda user: user.phone_number == phone_number, self._in_memory_database.users.values()))

        return users[0] if users else None

    def get_by_id(self, user_id: int) -> User:
        if (user := self._in_memory_database.users.get(user_id)) is None:
            raise UserNotFoundException

        return user

    def create(self, phone_number: str, name: str, tenant_id: int, is_registered: bool) -> User:
        if self.get_by_phone_number(phone_number=phone_number) is not None:
            raise PhoneNumberTakenException

        self._in_memory_database.users_id_seq += 1
        user = User(
            id=self._in_memory_database.users_id_seq,
            phone_number=phone_number,
            name=name,
            is_registered=is_registered,
            tenant_id=tenant_id,
        )

        self._in_memory_database.users[self._in_memory_database.users_id_seq] = user

        return user

    def update(self, user_id: int, tenant_id: int, name: str, is_registered: bool) -> User:
        if (user := self._in_memory_database.users.get(user_id)) is None:
            raise UserNotFoundException

        user.name = name
        user.is_registered = is_registered

        return user
