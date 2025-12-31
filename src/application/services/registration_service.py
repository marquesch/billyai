import secrets

from domain.entities import User
from domain.exceptions import KeyNotFoundException
from domain.exceptions import PhoneNumberTakenException
from domain.exceptions import RegistrationError
from domain.ports.repositories import CategoryRepository
from domain.ports.repositories import TenantRepository
from domain.ports.repositories import UserRepository
from domain.ports.services import TemporaryStorageService


class RegistrationService:
    def __init__(
        self,
        user_repository: UserRepository,
        tenant_repository: TenantRepository,
        category_repository: CategoryRepository,
        temporary_storage_service: TemporaryStorageService,
        user_validation_token_ttl_seconds: int,
    ):
        self._user_repository = user_repository
        self._tenant_repository = tenant_repository
        self._category_repository = category_repository
        self._temporary_storage_service = temporary_storage_service
        self._user_validation_token_ttl_seconds = user_validation_token_ttl_seconds

    def _get_user_data(self, token: str) -> dict:
        try:
            return self._temporary_storage_service.get(token)
        except KeyNotFoundException:
            raise RegistrationError("Invalid token")

    def initiate_registration(self, phone_number: str, name: str) -> str:
        if self._user_repository.get_by_phone_number(phone_number) is not None:
            raise PhoneNumberTakenException

        token = secrets.token_urlsafe(32)
        payload = {"phone_number": phone_number, "name": name}

        self._temporary_storage_service.set(token, payload, self._user_validation_token_ttl_seconds)

        return token

    def register_from_token(self, token: str) -> User:
        user_data = self._get_user_data(token)
        user = self.register(**user_data)
        self._temporary_storage_service.delete(token)

        return user

    def register(self, phone_number: str, name: str) -> User:
        tenant = self._tenant_repository.create()

        default_category = self._category_repository.create(
            tenant.id,
            "default",
            "Default category, for everything that doesn't fit other categories",
        )

        return self._user_repository.create(tenant_id=tenant.id, phone_number=phone_number, name=name)
