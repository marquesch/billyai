import secrets

from domain.entities import User
from domain.exceptions import KeyNotFoundException
from domain.exceptions import PhoneNumberTakenException
from domain.exceptions import RegistrationError
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository
from domain.ports.services import TemporaryStorageService

USER_VALIDATION_TOKEN_TTL_SECONDS = 1800


class RegistrationService:
    def __init__(
        self,
        user_repository: UserRepository,
        tenant_repository: TenantRepository,
        temporary_storage_service: TemporaryStorageService,
    ):
        self.user_repository = user_repository
        self.tenant_repository = tenant_repository
        self.temporary_storage_service = temporary_storage_service

    def initiate_registration(self, phone_number: str, name: str) -> str:
        if self.user_repository.get_by_phone_number(phone_number) is not None:
            raise PhoneNumberTakenException

        token = secrets.token_urlsafe(32)
        payload = {"phone_number": phone_number, "name": name}

        self.temporary_storage_service.set(token, payload, USER_VALIDATION_TOKEN_TTL_SECONDS)

        return token

    def register(self, token: str) -> User:
        try:
            user_data = self.temporary_storage_service.get(token)
        except KeyNotFoundException:
            raise RegistrationError("Invalid token")

        tenant = self.tenant_repository.create()

        self.temporary_storage_service.delete(token)
        user = self.user_repository.create(tenant_id=tenant.id, **user_data)

        return user
