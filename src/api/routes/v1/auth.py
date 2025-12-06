from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.dependencies import get_authentication_service
from api.dependencies import get_registration_service
from application.services.authentication_service import AuthenticationService
from application.services.registration_service import RegistrationService

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
    token = registration_service.initiate_registration(req.phone_number, req.name)

    # send task to celery
    print(token)

    return JSONResponse({"detail": "A confirmation link was sent to your phone"})


@router.get("/validation", name="user_validation")
async def register(
    token: str,
    registration_service: Annotated[RegistrationService, Depends(get_registration_service)],
):
    user = registration_service.register(token)

    return JSONResponse({"data": user})


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
    jwt_token = authentication_service.authorize_user(req.phone_number, req.pin)
    return JSONResponse({"token": jwt_token})
