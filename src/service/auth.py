import datetime
import json
import secrets
from string import Template
from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException

import tasks
from cfg import Session
from cfg import db_session
from core.models import Tenant
from core.models import User
from core.models.schema import UserModel
from libs import auth as auth_lib
from libs.cache import Cache
from libs.cache import get_cache

USER_PIN_TEMPLATE = Template("user:$user_id:pin")
USER_PIN_TTL_SECONDS = 1800
USER_VALIDATION_TOKEN_TTL_SECONDS = 1800


class AuthService:
    def __init__(self, cache: Cache, session: Session, base_url: str):
        self.cache = cache
        self.session = session
        self.base_url = base_url

    def generate_jwt_token(self, phone_number: str, pin: str) -> str:
        user = self._get_user(phone_number)

        if not self._check_user_pin(user, pin):
            raise HTTPException(404, "PIN not found")

        return auth_lib.generate_user_token(user)

    def generate_pin(self, phone_number: str) -> None:
        user = self._get_user(phone_number)

        pin = auth_lib.generate_pin()

        key = USER_PIN_TEMPLATE.substitute(user_id=user.id)
        self.cache.setex(key, datetime.timedelta(seconds=USER_PIN_TTL_SECONDS), pin)

        tasks.send_pin(phone_number, pin)

    def register(self, phone_number: str, name: str) -> None:
        user = User.get_by_phone_number(self.session, phone_number)

        if user is not None:
            raise HTTPException(409, "Phone number is already in use")

        token = secrets.token_urlsafe(32)
        token_ttl = datetime.timedelta(seconds=USER_VALIDATION_TOKEN_TTL_SECONDS)
        payload = {"phone_number": phone_number, "name": name}
        self.cache.setex(token, token_ttl, json.dumps(payload))

        confirmation_url = f"{self.base_url}/api/v1/auth/validation?token={token}"
        tasks.send_registration_confirmation_link.delay(phone_number, confirmation_url)

    def validate_user(self, token) -> User:
        raw_user_data = self.cache.get(token)
        if raw_user_data is None:
            raise HTTPException(404, "Token not found")

        user_data = UserModel.model_validate_json(raw_user_data)

        user = User.get_by_phone_number(self.session, user_data.phone_number)
        if user is not None:
            self.cache.delete(token)
            raise HTTPException(409, "Phone number is already in use")

        tenant = Tenant.new(self.session)
        user = User.new(self.session, user_data.name, user_data.phone_number, tenant_id=tenant.id)

        self.cache.delete(token)
        return user

    def _check_user_pin(self, user: User, pin: str) -> bool:
        raw_pin = self.cache.get(USER_PIN_TEMPLATE.substitute(user_id=user.id))

        return raw_pin is not None and raw_pin.decode("utf-8") == pin

    def _get_user(self, phone_number: str):
        user = User.get_by_phone_number(self.session, phone_number)

        if user is None:
            raise HTTPException(404, "User not found")

        return user


def get_auth_svc(
    cache: Annotated[Cache, Depends(get_cache)],
    session: Annotated[Session, Depends(db_session)],
) -> AuthService:
    return AuthService(cache=cache, session=session, base_url="http://localhost:8080")
