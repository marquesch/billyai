from domain.entities import User
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository


class GetOrCreateUserUseCase:
    def __init__(self, user_repository: UserRepository, tenant_repository: TenantRepository):
        self._user_repository = user_repository
        self._tenant_repository = tenant_repository

    def __call__(self, phone_number: str) -> User:
        user = self._user_repository.get_by_phone_number(phone_number)

        if user is not None:
            return user

        tenant = self._tenant_repository.create()

        return self._user_repository.create(phone_number, "", tenant.id)
