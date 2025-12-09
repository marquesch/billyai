from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from application.services.authentication_service import AuthenticationService
from application.services.registration_service import RegistrationService
from domain.exceptions import AuthError
from domain.exceptions import PhoneNumberTakenException
from domain.exceptions import RegistrationError
from presentation.api.dependencies import get_authentication_service
from presentation.api.dependencies import get_registration_service

router = APIRouter(prefix="/auth")


class RegisterUserRequest(BaseModel):
    name: str
    phone_number: str


class NewSessionRequest(BaseModel):
    phone_number: str
    pin: str


class NewPINRequest(BaseModel):
    phone_number: str


@router.post("/user")
async def initiate_registration(
    req: RegisterUserRequest,
    registration_service: Annotated[RegistrationService, Depends(get_registration_service)],
):
    try:
        token = registration_service.initiate_registration(req.phone_number, req.name)
    except PhoneNumberTakenException:
        raise HTTPException(409, detail="Phone number taken")

    # send task to celery
    print(token)

    return JSONResponse({"detail": "A confirmation link was sent to your phone"})


@router.post("/validation", name="user_validation")
async def register(
    token: str,
    registration_service: Annotated[RegistrationService, Depends(get_registration_service)],
):
    try:
        user = registration_service.register(token)
    except RegistrationError as e:
        raise HTTPException(422, detail="Invalid token") from e
    except PhoneNumberTakenException as e:
        raise HTTPException(409, detail="Phone number taken") from e

    return user


@router.post("/pin")
async def create_pin(
    req: NewPINRequest,
    authentication_service: Annotated[AuthenticationService, Depends(get_authentication_service)],
):
    pin = authentication_service.initiate_authorization(req.phone_number)

    # send task to celery
    print(pin)

    return JSONResponse({"message": "A PIN was sent to your phone"})


@router.post("/session")
async def create_session(
    req: NewSessionRequest,
    authentication_service: Annotated[AuthenticationService, Depends(get_authentication_service)],
):
    try:
        jwt_token = authentication_service.authorize_user(req.phone_number, req.pin)
    except AuthError as e:
        raise HTTPException(422, detail="Invalid PIN") from e

    return JSONResponse({"token": jwt_token})
