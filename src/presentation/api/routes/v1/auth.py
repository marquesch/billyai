import re
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from application.services.authentication_service import AuthenticationService
from application.services.registration_service import RegistrationService
from domain.exceptions import AuthError
from domain.exceptions import PhoneNumberTakenException
from domain.exceptions import RegistrationError
from presentation.api.dependencies import get_authentication_service
from presentation.api.dependencies import get_registration_service

router = APIRouter(prefix="/auth")


class PhoneNumberRequestMixin:
    phone_number: str = Field(
        pattern=r"^\(?([1-9]{2})\)?[\s-]?(?:9\d{4}|[2-5]\d{3})[\s-]?\d{4}$",
    )

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
        user = registration_service.register(token)
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
):
    pin = authentication_service.initiate_authorization(req.phone_number)

    # send task to celery
    print(pin)

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
