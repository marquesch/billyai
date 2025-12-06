import json
from typing import Any

import redis

from domain.exceptions import ResourceNotFoundException
from infrastructure.config import settings

pool = redis.ConnectionPool(host=settings.app_settings.redis_host, port=settings.app_settings.redis_port, db=0)


class RedisTemporaryStorageService:
    def __init__(self, redis_client: redis.Redis):
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
