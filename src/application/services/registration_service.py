import secrets

from domain.entities import User
from domain.exceptions import PhoneNumberTakenException
from domain.exceptions import RegistrationError
from domain.exceptions import ResourceNotFoundException
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
        except ResourceNotFoundException:
            raise RegistrationError("Invalid token")

        user = self.user_repository.get_by_phone_number(user_data.get("phone_number"))

        if user is not None:
            self.temporary_storage_service.delete(token)
            raise PhoneNumberTakenException

        tenant = self.tenant_repository.create()
        user = self.user_repository.create(user_data.get("phone_number"), user_data.get("name"), tenant_id=tenant.id)

        self.temporary_storage_service.delete(token)

        return user
