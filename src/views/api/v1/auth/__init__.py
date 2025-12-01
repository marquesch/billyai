import datetime
import json
import random
import secrets
import string
from typing import Annotated
from typing import Type

import jwt
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis import Redis

import tasks
from cfg import Session
from cfg import db_session
from core.models import Tenant
from core.models import User
from libs import auth
from libs.cache import Cache
from libs.cache import get_cache
from service.auth import AuthService
from service.auth import get_auth_svc

JWT_SECRET = "supersecret"
JWT_ALGORITHM = "HS256"

auth_router = APIRouter(prefix="/auth")


class RegisterUserRequest(BaseModel):
    name: str
    phone_number: str


class UserModel(BaseModel):
    name: str
    phone_number: str


class NewSessionRequest(BaseModel):
    phone_number: str
    pin: str


class NewPINRequest(BaseModel):
    phone_number: str


@auth_router.post("/user")
async def register(
    req: RegisterUserRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_svc)],
):
    auth_service.register(req.phone_number, req.name)

    return JSONResponse({"Detail": "A confirmation link was sent to your phone"})


@auth_router.get("/validation", name="user_validation")
async def user_validation(
    token: str,
    auth_service: Annotated[AuthService, Depends(get_auth_svc)],
):
    user = auth_service.validate_user(token)

    return JSONResponse({"data": user.to_dict()})


@auth_router.post("/pin")
async def new_pin(req: NewPINRequest, auth_service: Annotated[AuthService, Depends(get_auth_svc)]):
    auth_service.generate_pin(req.phone_number)

    return JSONResponse({"message": "A PIN was sent to your phone"})


@auth_router.post("/session")
async def new_session(req: NewSessionRequest, auth_service: Annotated[AuthService, Depends(get_auth_svc)]):
    return JSONResponse({"token": auth_service.generate_jwt_token(req.phone_number, req.pin)})
