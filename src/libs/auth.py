import datetime
import random
import string
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer

from cfg import Session
from cfg import db_session
from core.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/session")

JWT_SECRET = "supersecret"
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = 1800


def authenticated_user(
    session: Annotated[Session, Depends(db_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.exceptions.PyJWTError:
        raise credentials_exception

    user_phone_number = payload.get("sub")
    if user_phone_number is None:
        raise credentials_exception

    user = User.get_by_phone_number(session, user_phone_number)
    if user is None:
        raise credentials_exception

    return user


def generate_user_token(user: User) -> str:
    payload = {
        "sub": user.phone_number,
        "exp": datetime.datetime.now() + datetime.timedelta(seconds=JWT_TTL_SECONDS),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_pin() -> str:
    return "".join(random.choice(string.digits) for _ in range(6))
