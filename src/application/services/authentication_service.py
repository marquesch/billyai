import random
import string
from string import Template

from domain.entities import User
from domain.exceptions import AuthError
from domain.exceptions import DecodingError
from domain.exceptions import KeyNotFoundException
from domain.exceptions import UserNotFoundException
from domain.ports.repositories import UserRepository
from domain.ports.services import TemporaryStorageService
from domain.ports.services import UserEncodingService

USER_PIN_TEMPLATE = Template("user:$user_id:pin")


class AuthenticationService:
    def __init__(
        self,
        user_repository: UserRepository,
        temporary_storage_service: TemporaryStorageService,
        user_encoding_service: UserEncodingService,
        user_pin_ttl_seconds: int,
        user_token_ttl: int,
    ):
        self._user_repository = user_repository
        self._temporary_storage_service = temporary_storage_service
        self._user_encoding_service = user_encoding_service
        self._user_pin_ttl_seconds = user_pin_ttl_seconds
        self._user_token_ttl = user_token_ttl

    def authenticate_user(self, token: str) -> User:
        try:
            phone_number = self._user_encoding_service.decode(token)
        except DecodingError as e:
            raise AuthError("Invalid token") from e

        return self._user_repository.get_by_phone_number(phone_number)

    def initiate_authorization(self, phone_number: str) -> (str, User):
        user = self._user_repository.get_by_phone_number(phone_number)

        if user is None:
            raise UserNotFoundException

        pin = "".join(random.choice(string.digits) for _ in range(6))
        user_data = {"pin": pin, "user_phone": user.phone_number}
        key = USER_PIN_TEMPLATE.substitute(user_id=user.id)

        self._temporary_storage_service.set(key, user_data, self._user_pin_ttl_seconds)

        return pin, user

    def authorize_user(self, phone_number: str, pin: str) -> str:
        user = self._user_repository.get_by_phone_number(phone_number)

        temp_storage_key = USER_PIN_TEMPLATE.substitute(user_id=user.id)
        try:
            user_data = self._temporary_storage_service.get(temp_storage_key)
        except KeyNotFoundException as e:
            raise AuthError("Invalid PIN") from e

        if user_data["pin"] != pin:
            raise AuthError("Invalid PIN")

        self._temporary_storage_service.delete(temp_storage_key)
        return self._user_encoding_service.encode(phone_number, self._user_token_ttl)
