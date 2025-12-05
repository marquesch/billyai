import json
from typing import Any

from redis import Redis

from domain.exceptions import ResourceNotFoundException


class RedisTemporaryStorageService:
    def __init__(self, redis_client: Redis):
        self.client = redis_client

    def set(self, key: str, value: Any, expiration_seconds: int = -1) -> bool:
        json_data = json.dumps(value)
        return self.client.setex(key, expiration_seconds, json_data)

    def get(self, key: str) -> Any | None:
        json_data = self.client.get(key)

        if json_data is None:
            raise ResourceNotFoundException

        return json.loads(json_data)

    def delete(self, key: str) -> bool:
        return bool(self.client.delete(key))
