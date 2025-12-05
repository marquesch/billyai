import datetime

import jwt

from domain.exceptions import DecodingError

JWT_SECRET = "supersecret"
JWT_ALGORITHM = "HS256"


class JWTUserEncodingService:
    def encode(self, user_id: id, exp: int) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.datetime.now() + datetime.timedelta(seconds=exp),
        }

        return jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)

    def decode(self, token: str) -> int:
        try:
            payload = jwt.decode(token, algorithms=[JWT_ALGORITHM])
        except jwt.exceptions.PyJWTError as e:
            raise DecodingError from e

        if user_id := payload.get("sub") is None:
            raise DecodingError

        return user_id
