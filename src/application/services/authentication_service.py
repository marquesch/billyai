import random
import string
from string import Template

from domain.entities import User
from domain.exceptions import AuthenticationError
from domain.exceptions import AuthorizationError
from domain.exceptions import DecodingError
from domain.exceptions import ResourceNotFoundException
from domain.ports.repositories import UserRepository
from domain.ports.services import TemporaryStorageService
from domain.ports.services import UserEncodingService

USER_PIN_TEMPLATE = Template("user:$user_id:pin")
USER_PIN_TTL_SECONDS = 1800
USER_VALIDATION_TOKEN_TTL_SECONDS = 1800


class AuthenticationService:
    def __init__(
        self,
        user_repository: UserRepository,
        temporary_storage_service: TemporaryStorageService,
        user_encoding_service: UserEncodingService,
    ):
        self.user_repository = user_repository
        self.temporary_storage_service = temporary_storage_service
        self.user_encoding_service = user_encoding_service

    def _get_user_by_id(self, user_id):
        try:
            return self.user_repository.get_by_id(user_id)
        except ResourceNotFoundException as e:
            raise AuthenticationError("User not found") from e

    def authenticate_user(self, token: str) -> User:
        try:
            user_id = self.user_encoding_service.decode(token)
        except DecodingError as e:
            raise AuthenticationError("Decoding error") from e

        user = self._get_user_by_id(user_id)

        return user

    def initiate_authorization(self, user_id: int) -> str:
        user = self._get_user_by_id(user_id)

        pin = "".join(random.choice(string.digits) for _ in range(6))
        user_data = {"pin": pin, "user_phone": user.phone_number}
        key = USER_PIN_TEMPLATE.substitute(user_id=user_id)

        self.temporary_storage_service.set(key, user_data, USER_PIN_TTL_SECONDS)

        return pin

    def authorize_user(self, user_id: int, pin: str) -> str:
        try:
            user = self.user_repository.get_by_id(user_id)
        except ResourceNotFoundException as e:
            raise AuthorizationError("User not found") from e

        try:
            user_data = self.temporary_storage_service.get(USER_PIN_TEMPLATE.substitute(user_id=user.id))
        except ResourceNotFoundException:
            raise AuthorizationError("Invalid PIN")

        if user_data["pin"] != pin:
            raise AuthorizationError("Wrong PIN")

        return self.user_encoding_service.encode(user_id)
