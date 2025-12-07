import datetime

import jwt

from domain.exceptions import DecodingError

JWT_SECRET = "supersecret"
JWT_ALGORITHM = "HS256"


class JWTUserEncodingService:
    def encode(self, phone_number: str, exp: int) -> str:
        payload = {
            "sub": phone_number,
            "exp": datetime.datetime.now() + datetime.timedelta(seconds=exp),
        }

        return jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)

    def decode(self, token: str) -> str:
        try:
            payload = jwt.decode(token, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.exceptions.PyJWTError as e:
            raise DecodingError from e

        if (phone_number := payload.get("sub")) is None:
            raise DecodingError

        return phone_number
