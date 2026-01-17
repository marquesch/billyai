import datetime
import re
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import field_validator

from application.services.async_task_service import AsyncTaskService
from application.services.authentication_service import AuthenticationService
from application.services.registration_service import RegistrationService
from domain.entities import MessageAuthor
from domain.entities import MessageBroker
from domain.exceptions import AuthError
from domain.exceptions import PhoneNumberTakenException
from domain.exceptions import RegistrationError
from domain.exceptions import UserNotFoundException
from domain.ports.repositories import MessageRepository
from presentation.api import dependencies
from presentation.api.dependencies import get_authentication_service
from presentation.api.dependencies import get_registration_service

router = APIRouter(prefix="/auth")


class PhoneNumberRequestMixin:
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def format_phone_number(cls, v: str) -> str:
        return re.sub(r"\D", "", v)


class RegisterRequest(BaseModel, PhoneNumberRequestMixin):
    name: str


class VerifyLoginRequest(BaseModel, PhoneNumberRequestMixin):
    pin: str


class LoginRequest(BaseModel, PhoneNumberRequestMixin):
    pass


@router.post("/register")
async def register(
    req: RegisterRequest,
    registration_service: Annotated[
        RegistrationService,
        Depends(get_registration_service),
    ],
):
    try:
        token = registration_service.initiate_registration(req.phone_number, req.name)
    except PhoneNumberTakenException:
        raise HTTPException(409, detail="Phone number taken")

    # send task to celery
    print(token)

    return JSONResponse({"detail": "A confirmation link was sent to your phone"})


@router.post("/register/verify")
async def verify_registration(
    token: str,
    registration_service: Annotated[
        RegistrationService,
        Depends(get_registration_service),
    ],
):
    try:
        user = registration_service.register_from_token(token)
    except RegistrationError as e:
        raise HTTPException(422, detail="Invalid token") from e
    except PhoneNumberTakenException as e:
        raise HTTPException(409, detail="Phone number taken") from e

    return user


@router.post("/login")
async def login(
    req: LoginRequest,
    authentication_service: Annotated[
        AuthenticationService,
        Depends(get_authentication_service),
    ],
    message_repository: Annotated[MessageRepository, Depends(dependencies.get_message_repository)],
    async_task_service: Annotated[AsyncTaskService, Depends(dependencies.get_async_task_service)],
):
    try:
        pin, user = authentication_service.initiate_authorization(req.phone_number)
    except UserNotFoundException as e:
        raise HTTPException(404, detail="User not found") from e

    print(pin)

    message = message_repository.create(
        body=f"Seu PIN é {pin}",
        author=MessageAuthor.SYSTEM,
        timestamp=datetime.datetime.now(datetime.UTC),
        broker=MessageBroker.WHATSAPP,
        user_id=user.id,
        tenant_id=user.tenant_id,
    )

    await async_task_service.process_message.delay(message_id=message.id)

    return JSONResponse({"message": "A PIN was sent to your phone"})


@router.post("/login/verify")
async def verify_login(
    req: VerifyLoginRequest,
    authentication_service: Annotated[
        AuthenticationService,
        Depends(get_authentication_service),
    ],
):
    try:
        jwt_token = authentication_service.authorize_user(req.phone_number, req.pin)
    except AuthError as e:
        raise HTTPException(422, detail="Invalid PIN") from e

    return JSONResponse({"token": jwt_token})
